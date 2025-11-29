#!/usr/bin/env python3
"""
Startup script for VideoTranscript Pro with pre-flight validation.
"""
import os
import sys
import subprocess

def main():
    """Run validation and start the app."""
    print("=" * 60)
    print("VideoTranscript Pro - Starting Application")
    print("=" * 60)
    
    # Run validation first
    print("\nRunning pre-flight validation...\n")
    result = subprocess.run([sys.executable, "validate_app.py"], capture_output=False)
    
    if result.returncode != 0:
        print("\n❌ Validation failed. Please fix issues before starting.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Starting Flask application...")
    print("=" * 60 + "\n")
    
    # Set environment
    os.environ.setdefault("APP_ENV", "development")
    
    # Import and run the app
    from app import app
    
    debug = app.config.get("DEBUG", False)
    port = int(os.getenv("PORT", "5000"))
    
    print(f"Environment: {os.getenv('APP_ENV', 'development')}")
    print(f"Debug mode: {debug}")
    print(f"Port: {port}")
    print(f"\n🌐 Open your browser at: http://127.0.0.1:{port}")
    print("Press Ctrl+C to stop the server\n")
    print("=" * 60 + "\n")
    
    try:
        app.run(debug=debug, host="0.0.0.0", port=port, use_reloader=False)
    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
        sys.exit(0)

if __name__ == "__main__":
    main()

