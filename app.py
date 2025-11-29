"""
VideoTranscript Pro - Modern YouTube Transcript & Podcast Generator
A production-ready web application for extracting and processing YouTube transcripts
"""
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from flask_wtf.csrf import CSRFProtect
import logging
import os
import sys
from datetime import datetime
import uuid

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.youtube_podcast.utils.youtube_utils import fetch_transcript
from src.youtube_podcast.utils.bulk_extract import (
    bulk_extract_transcripts,
    parse_csv_urls,
    export_to_csv,
    export_transcripts_to_csv,
    get_playlist_video_ids,
)
from src.youtube_podcast.utils.auth import (
    requires_auth,
    requires_plan,
    check_token_limit,
    increment_token_usage,
)
from src.youtube_podcast.utils.supabase_client import get_supabase, is_supabase_configured
from src.youtube_podcast.utils.usage_tracker import track_usage, get_user_usage_history, get_user_usage_stats
from src.youtube_podcast.utils.rate_limiter import requires_rate_limit, check_rate_limit
from src.youtube_podcast.utils.payments import (
    is_stripe_configured,
    create_checkout_session,
    handle_stripe_webhook
)
from src.youtube_podcast.agents.summary_agent import (
    generate_summary,
)
from src.youtube_podcast.agents.podcast_agent import (
    create_conversation,
    generate_podcast,
)
from src.youtube_podcast.config.settings import DEFAULT_OUTPUT_DIR
from config import get_config


def create_app() -> Flask:
    """Application factory to create and configure the Flask app."""
    app = Flask(__name__)

    # Load environment-specific config
    cfg_cls = get_config()
    app.config.from_object(cfg_cls)
    
    # Initialize CSRF protection (exempt API endpoints that use token auth)
    csrf = CSRFProtect(app)
    
    # Exempt API endpoints from CSRF (they use token authentication)
    csrf.exempt('api_transcripts')
    csrf.exempt('api_channels')
    csrf.exempt('stripe_webhook')
    
    # Ensure SECRET_KEY is set securely in production
    if app.config.get("DEBUG") is False and not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "SECRET_KEY is not set. For production, configure SECRET_KEY in environment or config."
        )
    
    # Set default SECRET_KEY for development if not set
    if not app.config.get("SECRET_KEY"):
        import secrets
        app.config["SECRET_KEY"] = secrets.token_hex(32)
        logging.warning("SECRET_KEY not set. Using generated key for development only. Set SECRET_KEY in .env for production.")

    # Fallback for DEFAULT_OUTPUT_DIR if not using BaseConfig.OUTPUT_DIR
    output_dir = getattr(cfg_cls, "OUTPUT_DIR", DEFAULT_OUTPUT_DIR)
    app.config.setdefault("OUTPUT_DIR", output_dir)

    # Ensure output directory exists
    os.makedirs(app.config["OUTPUT_DIR"], exist_ok=True)

    # Configure basic logging
    log_level = app.config.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    logging.getLogger("werkzeug").setLevel(os.environ.get("WERKZEUG_LOG_LEVEL", "WARNING"))

    return app


app = create_app()

@app.route('/')
def home():
    """Home page"""
    return render_template('index.html')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/features')
def features():
    """Features page"""
    return render_template('features.html')

@app.route('/pricing')
def pricing():
    """Pricing page"""
    return render_template('pricing.html')

@app.route('/api')
def api_docs():
    """API documentation page"""
    return render_template('api.html')

@app.route('/support', endpoint='support')
def support():
    """Support page"""
    return render_template('support.html')

@app.route('/api/support/submit', methods=['POST'])
def submit_support_request():
    """Submit a support request"""
    try:
        if not session.get('user_id'):
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        category = data.get('category', '')
        subject = data.get('subject', '')
        message = data.get('message', '')
        
        if not category or not subject or not message:
            return jsonify({'error': 'All fields are required'}), 400
        
        # In production, save to database or send email
        # For now, just log it
        logging.info(f"Support request from {session.get('user_email')}: [{category}] {subject}")
        
        return jsonify({
            'success': True,
            'message': 'Support request submitted successfully. We\'ll respond within 24-48 hours.'
        })
    
    except Exception as e:
        return jsonify({'error': f'Error submitting request: {str(e)}'}), 500

@app.route('/login', endpoint='login')
def login():
    """Login page"""
    return render_template('login.html')

@app.route('/signup', endpoint='signup')
def signup():
    """Signup page (redirects to login with signup tab)"""
    return render_template('login.html')

@app.route('/auth/login', methods=['POST'])
def auth_login():
    """Handle user login"""
    try:
        if not is_supabase_configured():
            return jsonify({'error': 'Authentication service not configured'}), 500
        
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        supabase = get_supabase()
        response = supabase.auth.sign_in_with_password({
            'email': email,
            'password': password
        })
        
        if response.user:
            # Store user session
            user_id = str(response.user.id)
            session['user_id'] = user_id
            session['user_email'] = response.user.email
            session['access_token'] = response.session.access_token
            
            # Ensure user profile exists (should be created by trigger, but verify)
            try:
                supabase = get_supabase()
                profile_check = supabase.table('user_profiles').select('id').eq('id', user_id).execute()
                if not profile_check.data:
                    # Create profile if trigger didn't fire
                    supabase.table('user_profiles').insert({
                        'id': user_id,
                        'email': response.user.email,
                        'plan': 'free',
                        'tokens_limit': 25
                    }).execute()
            except Exception as e:
                logging.warning(f"Could not verify user profile: {str(e)}")
            
            return jsonify({
                'success': True,
                'user': {
                    'id': user_id,
                    'email': response.user.email
                },
                'redirect': url_for('home')
            })
        else:
            return jsonify({'error': 'Invalid email or password'}), 401
    
    except Exception as e:
        error_msg = str(e)
        if 'Invalid login credentials' in error_msg:
            return jsonify({'error': 'Invalid email or password'}), 401
        return jsonify({'error': f'Login failed: {error_msg}'}), 500

@app.route('/auth/signup', methods=['POST'])
def auth_signup():
    """Handle user signup"""
    try:
        if not is_supabase_configured():
            return jsonify({'error': 'Authentication service not configured'}), 500
        
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        supabase = get_supabase()
        response = supabase.auth.sign_up({
            'email': email,
            'password': password
        })
        
        if response.user:
            user_id = str(response.user.id)
            
            # User profile should be created by database trigger, but verify
            try:
                profile_check = supabase.table('user_profiles').select('id').eq('id', user_id).execute()
                if not profile_check.data:
                    # Create profile if trigger didn't fire
                    supabase.table('user_profiles').insert({
                        'id': user_id,
                        'email': email,
                        'plan': 'free',
                        'tokens_limit': 25
                    }).execute()
            except Exception as e:
                logging.warning(f"Could not verify user profile creation: {str(e)}")
            
            return jsonify({
                'success': True,
                'message': 'Account created successfully. Please check your email to verify your account.',
                'user': {
                    'id': user_id,
                    'email': response.user.email
                },
                'redirect': url_for('login')
            })
        else:
            return jsonify({'error': 'Failed to create account'}), 400
    
    except Exception as e:
        error_msg = str(e)
        if 'User already registered' in error_msg or 'already registered' in error_msg.lower():
            return jsonify({'error': 'An account with this email already exists'}), 400
        return jsonify({'error': f'Signup failed: {error_msg}'}), 500

@app.route('/auth/logout', methods=['POST'])
def auth_logout():
    """Handle user logout"""
    try:
        if is_supabase_configured():
            supabase = get_supabase()
            if session.get('access_token'):
                supabase.auth.sign_out()
        
        session.clear()
        return jsonify({
            'success': True,
            'redirect': url_for('home')
        })
    
    except Exception as e:
        session.clear()
        return jsonify({
            'success': True,
            'redirect': url_for('home')
        })

@app.route('/auth/google', methods=['POST'])
def auth_google():
    """Initiate Google OAuth login"""
    try:
        if not is_supabase_configured():
            return jsonify({'error': 'Authentication service not configured'}), 500
        
        supabase = get_supabase()
        response = supabase.auth.sign_in_with_oauth({
            'provider': 'google',
            'options': {
                'redirect_to': request.host_url.rstrip('/') + url_for('auth_callback')
            }
        })
        
        if response.url:
            return jsonify({'success': True, 'url': response.url})
        else:
            return jsonify({'error': 'Failed to initiate Google login'}), 500
    
    except Exception as e:
        return jsonify({'error': f'Google login failed: {str(e)}'}), 500

@app.route('/auth/microsoft', methods=['POST'])
def auth_microsoft():
    """Initiate Microsoft OAuth login"""
    try:
        if not is_supabase_configured():
            return jsonify({'error': 'Authentication service not configured'}), 500
        
        supabase = get_supabase()
        response = supabase.auth.sign_in_with_oauth({
            'provider': 'azure',
            'options': {
                'redirect_to': request.host_url.rstrip('/') + url_for('auth_callback')
            }
        })
        
        if response.url:
            return jsonify({'success': True, 'url': response.url})
        else:
            return jsonify({'error': 'Failed to initiate Microsoft login'}), 500
    
    except Exception as e:
        return jsonify({'error': f'Microsoft login failed: {str(e)}'}), 500

@app.route('/auth/callback')
def auth_callback():
    """Handle OAuth callback"""
    try:
        code = request.args.get('code')
        if not code:
            return redirect(url_for('login'))
        
        supabase = get_supabase()
        response = supabase.auth.get_session()
        
        if response.session and response.user:
            session['user_id'] = str(response.user.id)
            session['user_email'] = response.user.email
            session['access_token'] = response.session.access_token
            return redirect(url_for('home'))
        else:
            return redirect(url_for('login'))
    
    except Exception as e:
        print(f"Auth callback error: {str(e)}")
        return redirect(url_for('login'))

@app.route('/account', endpoint='account')
def account():
    """User account page"""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    return render_template('account.html')

@app.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    """Get user profile information with usage stats"""
    try:
        if not session.get('user_id'):
            return jsonify({'error': 'Not authenticated'}), 401
        
        if not is_supabase_configured():
            return jsonify({'error': 'Database not configured'}), 500
        
        supabase = get_supabase()
        user_id = session.get('user_id')
        
        # Get user profile from database
        response = supabase.table('user_profiles').select('*').eq('id', user_id).execute()
        
        if response.data and len(response.data) > 0:
            profile = response.data[0]
            # Get usage stats
            usage_stats = get_user_usage_stats(user_id)
            profile.update(usage_stats)
            
            return jsonify({
                'success': True,
                'profile': profile
            })
        else:
            # Create default profile if doesn't exist
            supabase.table('user_profiles').insert({
                'id': user_id,
                'email': session.get('user_email'),
                'plan': 'free',
                'tokens_limit': 25
            }).execute()
            
            return jsonify({
                'success': True,
                'profile': {
                    'id': user_id,
                    'email': session.get('user_email'),
                    'plan': 'free',
                    'tokens_used': 0,
                    'tokens_limit': 25,
                    'total_operations': 0,
                    'tokens_remaining': 25
                }
            })
    
    except Exception as e:
        return jsonify({'error': f'Error fetching profile: {str(e)}'}), 500

@app.route('/api/user/usage-history', methods=['GET'])
def get_usage_history():
    """Get user's usage history"""
    try:
        if not session.get('user_id'):
            return jsonify({'error': 'Not authenticated'}), 401
        
        limit = request.args.get('limit', 50, type=int)
        history = get_user_usage_history(session.get('user_id'), limit)
        
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })
    
    except Exception as e:
        return jsonify({'error': f'Error fetching usage history: {str(e)}'}), 500

@app.route('/api/user/tokens', methods=['GET', 'POST'])
def manage_api_tokens():
    """Get or create API tokens - Connected to Supabase"""
    try:
        if not session.get('user_id'):
            return jsonify({'error': 'Not authenticated'}), 401
        
        if not is_supabase_configured():
            return jsonify({'error': 'Database not configured'}), 500
        
        supabase = get_supabase()
        user_id = session.get('user_id')
        
        if request.method == 'GET':
            # Get all tokens for user from Supabase
            try:
                response = supabase.table('api_tokens').select('*').eq('user_id', user_id).execute()
                return jsonify({
                    'success': True,
                    'tokens': response.data or []
                })
            except Exception as e:
                logging.error(f"Error fetching tokens from Supabase: {str(e)}")
                return jsonify({'error': f'Database error: {str(e)}'}), 500
        
        elif request.method == 'POST':
            # Generate new API token and save to Supabase
            import secrets
            new_token = f"vtp_{secrets.token_urlsafe(32)}"
            
            try:
                # Insert token into Supabase
                response = supabase.table('api_tokens').insert({
                    'user_id': user_id,
                    'token': new_token,
                    'name': f'Token {datetime.now().strftime("%Y-%m-%d")}'
                }).execute()
                
                # Also update in-memory cache for immediate use
                from src.youtube_podcast.utils.auth import API_TOKENS
                API_TOKENS[new_token] = {
                    "plan": "free",  # Will be updated from user profile
                    "tokens_used": 0,
                    "tokens_limit": 25,
                    "monthly_reset": True,
                    "user_id": user_id
                }
                
                # Get user plan from profile
                profile_response = supabase.table('user_profiles').select('plan, tokens_limit').eq('id', user_id).execute()
                if profile_response.data:
                    plan = profile_response.data[0].get('plan', 'free')
                    tokens_limit = profile_response.data[0].get('tokens_limit', 25)
                    API_TOKENS[new_token]['plan'] = plan
                    API_TOKENS[new_token]['tokens_limit'] = tokens_limit
                
                return jsonify({
                    'success': True,
                    'token': new_token,
                    'message': 'Token created successfully and saved to database'
                })
            except Exception as e:
                logging.error(f"Error creating token in Supabase: {str(e)}")
                return jsonify({'error': f'Database error: {str(e)}'}), 500
    
    except Exception as e:
        logging.error(f"Error managing tokens: {str(e)}")
        return jsonify({'error': f'Error managing tokens: {str(e)}'}), 500

@app.route('/api/user/tokens/<token_id>', methods=['DELETE'])
def delete_api_token(token_id):
    """Delete an API token from Supabase"""
    try:
        if not session.get('user_id'):
            return jsonify({'error': 'Not authenticated'}), 401
        
        if not is_supabase_configured():
            return jsonify({'error': 'Database not configured'}), 500
        
        supabase = get_supabase()
        user_id = session.get('user_id')
        
        # Get token before deleting (to remove from cache)
        token_response = supabase.table('api_tokens').select('token').eq('id', token_id).eq('user_id', user_id).execute()
        
        # Delete from Supabase
        response = supabase.table('api_tokens').delete().eq('id', token_id).eq('user_id', user_id).execute()
        
        # Also remove from in-memory cache
        if token_response.data:
            token = token_response.data[0].get('token')
            from src.youtube_podcast.utils.auth import API_TOKENS
            if token in API_TOKENS:
                del API_TOKENS[token]
        
        return jsonify({
            'success': True,
            'message': 'Token deleted successfully from database'
        })
    
    except Exception as e:
        logging.error(f"Error deleting token: {str(e)}")
        return jsonify({'error': f'Error deleting token: {str(e)}'}), 500


@app.route("/healthz", methods=["GET"])
def health_check():
    """Simple health-check endpoint for load balancers and uptime monitoring."""
    return jsonify({"status": "ok", "service": "video-transcript-pro"}), 200

@app.route('/favicon.ico')
def favicon():
    """Handle favicon requests to avoid noisy 404 logs."""
    # You can later replace this with a real favicon file served from /static.
    # Returning 204 (No Content) keeps logs clean without affecting the UI.
    return ("", 204)

@app.route('/extract', methods=['POST'])
@requires_rate_limit
def extract_transcript():
    """Extract transcript from YouTube URL"""
    try:
        data = request.get_json()
        youtube_url = data.get('url', '').strip()
        
        if not youtube_url:
            return jsonify({'error': 'YouTube URL is required'}), 400
        
        # Fetch transcript
        transcript = fetch_transcript(youtube_url)
        
        if not transcript:
            return jsonify({'error': 'Failed to fetch transcript. The video may not have captions available.'}), 400
        
        # Store in session for later use
        session_id = str(uuid.uuid4())
        session[session_id] = {
            'transcript': transcript,
            'url': youtube_url,
            'timestamp': datetime.now().isoformat()
        }
        
        # Track usage if user is logged in
        if session.get('user_id'):
            track_usage(
                user_id=session.get('user_id'),
                video_url=youtube_url,
                operation_type='extract',
                transcript_length=len(transcript),
                tokens_used=1
            )
        
        return jsonify({
            'success': True,
            'transcript': transcript,
            'session_id': session_id,
            'length': len(transcript)
        })
    
    except Exception as e:
        return jsonify({'error': f'Error processing request: {str(e)}'}), 500

@app.route('/generate-summary', methods=['POST'])
@requires_rate_limit
def generate_summary_endpoint():
    """Generate summary from transcript"""
    try:
        data = request.get_json()
        transcript = data.get('transcript', '')
        session_id = data.get('session_id', '')
        
        if not transcript:
            return jsonify({'error': 'Transcript is required'}), 400
        
        # Create state dictionary
        state = {
            'url': data.get('url', ''),
            'transcript': transcript,
            'status': 'transcript_fetched',
            'output_type': 'summary'
        }
        
        # Generate summary
        result = generate_summary(state)
        
        if result.get('error'):
            return jsonify({'error': result['error']}), 500
        
        # Track usage if user is logged in
        if session.get('user_id'):
            track_usage(
                user_id=session.get('user_id'),
                video_url=data.get('url', ''),
                operation_type='summary',
                transcript_length=len(transcript),
                tokens_used=1
            )
        
        return jsonify({
            'success': True,
            'summary': result.get('summary', ''),
            'title': result.get('summary_title', 'Summary'),
            'filename': os.path.basename(result.get('summary_filename', ''))
        })
    
    except Exception as e:
        return jsonify({'error': f'Error generating summary: {str(e)}'}), 500

@app.route('/generate-podcast', methods=['POST'])
@requires_rate_limit
def generate_podcast_endpoint():
    """Generate podcast from transcript"""
    try:
        data = request.get_json()
        transcript = data.get('transcript', '')
        gender = data.get('gender', 'mixed')
        
        if not transcript:
            return jsonify({'error': 'Transcript is required'}), 400
        
        # Create state dictionary
        state = {
            'url': data.get('url', ''),
            'transcript': transcript,
            'status': 'transcript_fetched',
            'output_type': 'podcast',
            'gender': gender
        }
        
        # Generate conversation
        state = create_conversation(state)
        
        if state.get('error'):
            return jsonify({'error': state['error']}), 500
        
        # Generate audio
        state = generate_podcast(state)
        
        if state.get('error'):
            return jsonify({'error': state['error']}), 500
        
        audio_path = state.get('audio_path')
        if not audio_path or not os.path.exists(audio_path):
            return jsonify({'error': 'Failed to generate audio file'}), 500
        
        # Track usage if user is logged in
        if session.get('user_id'):
            track_usage(
                user_id=session.get('user_id'),
                video_url=data.get('url', ''),
                operation_type='podcast',
                transcript_length=len(transcript),
                tokens_used=1
            )
        
        return jsonify({
            'success': True,
            'conversation': state.get('conversation', ''),
            'title': state.get('podcast_title', 'Podcast'),
            'audio_filename': os.path.basename(audio_path),
            'audio_url': f'/download/{os.path.basename(audio_path)}'
        })
    
    except Exception as e:
        return jsonify({'error': f'Error generating podcast: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download generated files"""
    try:
        file_path = os.path.join(DEFAULT_OUTPUT_DIR, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True)
    
    except Exception as e:
        return jsonify({'error': f'Error downloading file: {str(e)}'}), 500

@app.route('/bulk-extract', methods=['POST'])
def bulk_extract_endpoint():
    """Extract transcripts from multiple YouTube URLs"""
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        
        if not urls or not isinstance(urls, list):
            return jsonify({'error': 'URLs list is required'}), 400
        
        if len(urls) > 50:  # Limit to 50 videos per request
            return jsonify({'error': 'Maximum 50 URLs allowed per request'}), 400
        
        results = bulk_extract_transcripts(urls)
        
        return jsonify({
            'success': True,
            'results': results,
            'total': len(results),
            'successful': sum(1 for r in results if r.get('success')),
            'failed': sum(1 for r in results if not r.get('success'))
        })
    
    except Exception as e:
        return jsonify({'error': f'Error processing bulk extraction: {str(e)}'}), 500

@app.route('/api/transcripts', methods=['POST'])
@requires_auth
def api_transcripts():
    """
    API endpoint to fetch transcripts for multiple video IDs.
    Requires authentication via API token.
    """
    try:
        data = request.get_json()
        video_ids = data.get('ids', [])
        
        if not video_ids or not isinstance(video_ids, list):
            return jsonify({'error': 'ids array is required'}), 400
        
        if len(video_ids) > 50:
            return jsonify({'error': 'Maximum 50 video IDs allowed per request'}), 400
        
        # Check token limit
        has_limit, error_msg = check_token_limit(request.api_token, len(video_ids))
        if not has_limit:
            return jsonify({'error': error_msg}), 403
        
        # Convert video IDs to URLs
        urls = [f'https://www.youtube.com/watch?v={vid}' for vid in video_ids]
        results = bulk_extract_transcripts(urls)
        
        # Increment token usage in cache and database
        increment_token_usage(request.api_token, len(video_ids))
        
        # Update database token usage
        if hasattr(request, 'api_user_id') and request.api_user_id:
            from src.youtube_podcast.utils.usage_tracker import update_user_token_usage
            update_user_token_usage(request.api_user_id, len(video_ids))
        
        # Format response similar to youtube-transcript.io
        formatted_results = []
        for result in results:
            formatted_results.append({
                'video_id': result.get('video_id'),
                'transcript': result.get('transcript', ''),
                'success': result.get('success', False),
                'error': result.get('error')
            })
        
        return jsonify({
            'success': True,
            'results': formatted_results,
            'total': len(results),
            'successful': sum(1 for r in results if r.get('success'))
        })
    
    except Exception as e:
        return jsonify({'error': f'Error processing request: {str(e)}'}), 500

@app.route('/api/channels', methods=['POST'])
@requires_plan('plus')
def api_channels():
    """
    API endpoint to fetch channel information.
    Requires Plus plan or higher.
    """
    try:
        data = request.get_json()
        channel_ids = data.get('ids', [])
        include_playlist_data = data.get('includePlaylistData', False)
        
        if not channel_ids or not isinstance(channel_ids, list):
            return jsonify({'error': 'ids array is required'}), 400
        
        # Plan-based limits
        user_plan = request.user_plan
        if user_plan == 'plus' and len(channel_ids) > 5:
            return jsonify({'error': 'Plus plan limited to 5 channels per request'}), 400
        elif len(channel_ids) > 50:
            return jsonify({'error': 'Maximum 50 channels allowed per request'}), 400
        
        # Placeholder response - requires YouTube Data API integration
        return jsonify({
            'success': True,
            'message': 'Channel API requires YouTube Data API v3 integration',
            'note': 'This endpoint is ready but needs YouTube Data API key configuration',
            'channels_requested': len(channel_ids),
            'include_playlist_data': include_playlist_data
        })
    
    except Exception as e:
        return jsonify({'error': f'Error processing request: {str(e)}'}), 500

@app.route('/extract-playlist', methods=['POST'])
@requires_auth
def extract_playlist_endpoint():
    """Extract transcripts from a YouTube playlist (requires authentication)"""
    try:
        data = request.get_json()
        playlist_url = data.get('playlist_url', '').strip()
        
        if not playlist_url:
            return jsonify({'error': 'Playlist URL is required'}), 400
        
        video_ids = get_playlist_video_ids(playlist_url)
        
        if not video_ids:
            return jsonify({
                'error': 'Could not extract video IDs from playlist. YouTube Data API key may be required.',
                'note': 'Playlist extraction requires YouTube Data API v3 access'
            }), 400
        
        # Check token limit
        has_limit, error_msg = check_token_limit(request.api_token, len(video_ids))
        if not has_limit:
            return jsonify({'error': error_msg}), 403
        
        # Convert video IDs to full URLs
        urls = [f'https://www.youtube.com/watch?v={vid}' for vid in video_ids]
        results = bulk_extract_transcripts(urls)
        
        # Increment token usage
        increment_token_usage(request.api_token, len(video_ids))
        
        return jsonify({
            'success': True,
            'playlist_url': playlist_url,
            'results': results,
            'total': len(results),
            'successful': sum(1 for r in results if r.get('success'))
        })
    
    except Exception as e:
        return jsonify({'error': f'Error processing playlist: {str(e)}'}), 500

@app.route('/import-csv', methods=['POST'])
def import_csv_endpoint():
    """Import YouTube URLs from CSV and extract transcripts"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'CSV file is required'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'File must be a CSV'}), 400
        
        csv_content = file.read().decode('utf-8')
        urls = parse_csv_urls(csv_content)
        
        if not urls:
            return jsonify({'error': 'No YouTube URLs found in CSV'}), 400
        
        if len(urls) > 50:
            return jsonify({'error': 'Maximum 50 URLs allowed per CSV'}), 400
        
        results = bulk_extract_transcripts(urls)
        
        return jsonify({
            'success': True,
            'urls_found': len(urls),
            'results': results,
            'total': len(results),
            'successful': sum(1 for r in results if r.get('success'))
        })
    
    except Exception as e:
        return jsonify({'error': f'Error processing CSV: {str(e)}'}), 500

@app.route('/export-csv', methods=['POST'])
def export_csv_endpoint():
    """Export extraction results to CSV"""
    try:
        data = request.get_json()
        results = data.get('results', [])
        export_full = data.get('export_full', False)  # If True, include full transcripts
        
        if not results:
            return jsonify({'error': 'No results to export'}), 400
        
        if export_full:
            csv_content = export_transcripts_to_csv(results)
            filename = 'transcripts_full.csv'
        else:
            csv_content = export_to_csv(results)
            filename = 'transcripts_summary.csv'
        
        # Save to output directory
        file_path = os.path.join(DEFAULT_OUTPUT_DIR, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'download_url': f'/download/{filename}'
        })
    
    except Exception as e:
        return jsonify({'error': f'Error exporting CSV: {str(e)}'}), 500

@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return render_template('404.html'), 404

@app.route('/api/payment/create-checkout', methods=['POST'])
def create_payment_checkout():
    """Create Stripe checkout session for subscription"""
    try:
        if not session.get('user_id'):
            return jsonify({'error': 'Authentication required'}), 401
        
        if not is_stripe_configured():
            return jsonify({'error': 'Payment service not configured'}), 500
        
        data = request.get_json()
        plan = data.get('plan', '').lower()
        
        if plan not in ['plus', 'pro', 'enterprise']:
            return jsonify({'error': 'Invalid plan selected'}), 400
        
        # Map plans to Stripe Price IDs (configure in environment)
        price_ids = {
            'plus': os.getenv('STRIPE_PRICE_PLUS', ''),
            'pro': os.getenv('STRIPE_PRICE_PRO', ''),
            'enterprise': os.getenv('STRIPE_PRICE_ENTERPRISE', '')
        }
        
        price_id = price_ids.get(plan)
        if not price_id:
            return jsonify({'error': f'Price ID not configured for {plan} plan'}), 500
        
        user_id = session.get('user_id')
        user_email = session.get('user_email', '')
        
        result = create_checkout_session(user_id, user_email, plan, price_id)
        
        if result:
            return jsonify({
                'success': True,
                'session_id': result['session_id'],
                'url': result['url']
            })
        else:
            return jsonify({'error': 'Failed to create checkout session'}), 500
    
    except Exception as e:
        logging.error(f"Error creating checkout session: {str(e)}")
        return jsonify({'error': f'Payment error: {str(e)}'}), 500

@app.route('/api/payment/webhook', methods=['POST'])
@csrf.exempt  # Webhook must be exempt from CSRF (Stripe verifies via signature)
def stripe_webhook():
    """Handle Stripe webhook events"""
    try:
        payload = request.data
        signature = request.headers.get('Stripe-Signature')
        
        if not signature:
            return jsonify({'error': 'Missing signature'}), 400
        
        if handle_stripe_webhook(payload, signature):
            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Webhook processing failed'}), 400
    
    except Exception as e:
        logging.error(f"Error handling webhook: {str(e)}")
        return jsonify({'error': f'Webhook error: {str(e)}'}), 500

@app.route('/api/user/usage-history', methods=['GET'])
def get_usage_history():
    """Get user's usage history"""
    try:
        if not session.get('user_id'):
            return jsonify({'error': 'Authentication required'}), 401
        
        limit = request.args.get('limit', 50, type=int)
        user_id = session.get('user_id')
        
        history = get_user_usage_history(user_id, limit)
        
        return jsonify({
            'success': True,
            'history': history,
            'total': len(history)
        })
    
    except Exception as e:
        logging.error(f"Error fetching usage history: {str(e)}")
        return jsonify({'error': f'Error fetching history: {str(e)}'}), 500

@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Run the Flask app (debug controlled by config / environment)
    debug = app.config.get("DEBUG", False)
    port = int(os.getenv("PORT", "5000"))

    print("=" * 50)
    print("VideoTranscript Pro - Starting Flask Application")
    print("=" * 50)
    print(f"Environment: {os.getenv('APP_ENV') or os.getenv('FLASK_ENV') or 'development'}")
    print(f"Debug: {debug}")
    print(f"Open your browser at: http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)

    app.run(debug=debug, host="0.0.0.0", port=port)

