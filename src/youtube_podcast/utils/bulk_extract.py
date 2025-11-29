"""
Bulk extraction utilities for YouTube transcripts.
Supports playlists, channels, and CSV imports.
"""
from typing import List, Dict, Optional
from youtube_transcript_api import YouTubeTranscriptApi
import re
import csv
import io
from .youtube_utils import extract_video_id, fetch_transcript


def extract_playlist_id(url: str) -> Optional[str]:
    """Extract playlist ID from YouTube playlist URL."""
    patterns = [
        r'[?&]list=([a-zA-Z0-9_-]+)',
        r'/playlist\?list=([a-zA-Z0-9_-]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_playlist_video_ids(playlist_url: str) -> List[str]:
    """
    Get all video IDs from a YouTube playlist.
    Note: This requires the googleapiclient library for full functionality.
    For now, returns a placeholder that can be extended.
    """
    try:
        # This is a simplified version. Full implementation would use YouTube Data API
        # For now, we'll extract video IDs from the playlist page or use a library
        playlist_id = extract_playlist_id(playlist_url)
        if not playlist_id:
            return []
        
        # Placeholder: In production, use YouTube Data API v3
        # from googleapiclient.discovery import build
        # youtube = build('youtube', 'v3', developerKey=API_KEY)
        # request = youtube.playlistItems().list(part='contentDetails', playlistId=playlist_id, maxResults=50)
        # response = request.execute()
        # return [item['contentDetails']['videoId'] for item in response.get('items', [])]
        
        # For now, return empty list - requires YouTube Data API key
        return []
    except Exception as e:
        print(f"Error getting playlist videos: {str(e)}")
        return []


def extract_channel_id(url: str) -> Optional[str]:
    """Extract channel ID from YouTube channel URL."""
    patterns = [
        r'/channel/([a-zA-Z0-9_-]+)',
        r'/c/([a-zA-Z0-9_-]+)',
        r'/user/([a-zA-Z0-9_-]+)',
        r'@([a-zA-Z0-9_-]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def bulk_extract_transcripts(urls: List[str]) -> List[Dict[str, any]]:
    """
    Extract transcripts from multiple YouTube video URLs.
    
    Args:
        urls: List of YouTube video URLs
        
    Returns:
        List of dictionaries with 'url', 'video_id', 'transcript', 'success', 'error'
    """
    results = []
    for url in urls:
        try:
            video_id = extract_video_id(url)
            transcript = fetch_transcript(url)
            
            results.append({
                'url': url,
                'video_id': video_id,
                'transcript': transcript,
                'success': transcript is not None,
                'error': None if transcript else 'Failed to fetch transcript'
            })
        except Exception as e:
            results.append({
                'url': url,
                'video_id': None,
                'transcript': None,
                'success': False,
                'error': str(e)
            })
    
    return results


def parse_csv_urls(csv_content: str) -> List[str]:
    """
    Parse YouTube URLs from CSV content.
    Expects CSV with a column containing YouTube URLs.
    """
    urls = []
    try:
        reader = csv.DictReader(io.StringIO(csv_content))
        for row in reader:
            # Look for URL in any column
            for value in row.values():
                if value and ('youtube.com' in value or 'youtu.be' in value):
                    urls.append(value.strip())
    except Exception as e:
        print(f"Error parsing CSV: {str(e)}")
    
    return urls


def export_to_csv(results: List[Dict[str, any]], filename: str = None) -> str:
    """
    Export bulk extraction results to CSV format.
    
    Args:
        results: List of extraction results
        filename: Optional filename (not used, returns CSV string)
        
    Returns:
        CSV content as string
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['URL', 'Video ID', 'Success', 'Transcript Length', 'Error'])
    
    # Write data
    for result in results:
        transcript_length = len(result.get('transcript', '')) if result.get('transcript') else 0
        writer.writerow([
            result.get('url', ''),
            result.get('video_id', ''),
            result.get('success', False),
            transcript_length,
            result.get('error', '')
        ])
    
    return output.getvalue()


def export_transcripts_to_csv(results: List[Dict[str, any]]) -> str:
    """
    Export full transcripts to CSV (one row per video with full transcript).
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['URL', 'Video ID', 'Transcript'])
    
    # Write data
    for result in results:
        if result.get('success') and result.get('transcript'):
            writer.writerow([
                result.get('url', ''),
                result.get('video_id', ''),
                result.get('transcript', '')
            ])
    
    return output.getvalue()

