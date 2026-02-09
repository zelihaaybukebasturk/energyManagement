"""
Simple HTTP server to serve the frontend.
Run this to serve the frontend on http://localhost:8080
"""

import http.server
import socketserver
import os
from pathlib import Path

PORT = 8080
FRONTEND_DIR = Path(__file__).parent / "frontend"

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == "__main__":
    os.chdir(FRONTEND_DIR)
    
    # Redirect root to login
    class RedirectHandler(MyHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/' or self.path == '/index.html':
                self.send_response(301)
                self.send_header('Location', '/login.html')
                self.end_headers()
            else:
                super().do_GET()
    
    with socketserver.TCPServer(("", PORT), RedirectHandler) as httpd:
        print(f"Frontend server running at http://localhost:{PORT}/")
        print(f"Serving files from: {FRONTEND_DIR}")
        print("\nMake sure the backend API is running on http://localhost:8000")
        print("Access the app at: http://localhost:8080/login.html")
        print("Press Ctrl+C to stop the server\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
