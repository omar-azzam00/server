import socket
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote
import os

class ThreadedHTTPHandler(SimpleHTTPRequestHandler):

    def log_message(self, format, *args):
        """Override to suppress log messages (removes default status prints)."""
        pass

    def send_response(self, code, message=None):
        """Override to send keep-alive headers."""
        super().send_response(code, message)
        self.send_header("Connection", "keep-alive")
        self.send_header("Keep-Alive", "timeout=5, max=100")

    def do_GET(self):
        """Handle GET requests."""
        file_path = self.translate_path(unquote(self.path))

        # Check if the file exists and is a video
        if os.path.isfile(file_path) and file_path.endswith(('.mp4', '.mkv', '.avi')):
            try:
                self.stream_file(file_path)
            except Exception as e:
                self.send_error(500, f"Internal server error: {e}")
        else:
            # Serve the file or directory if not a video or if a directory is requested
            super().do_GET()

    def stream_file(self, file_path):
        """Serve a large file efficiently."""
        file_size = os.path.getsize(file_path)
        self.send_response(200)
        self.send_header("Content-type", "video/mp4")  # For video files, change content type if needed
        self.send_header("Content-Length", str(file_size))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()

        # Serve the file in chunks for efficient streaming
        with open(file_path, 'rb') as file:
            chunk_size = 1024 * 1024  # Serve in 1MB chunks to balance memory and performance
            while chunk := file.read(chunk_size):
                self.wfile.write(chunk)

def get_private_ip():
    """Fetch the private IP address of the device on the home network."""
    try:
        # Use a socket to connect to a common external IP and get the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))  # Google's public DNS server (doesn't actually send a packet)
        private_ip = s.getsockname()[0]
        s.close()
    except Exception as e:
        private_ip = f"Unable to determine IP: {e}"
    return private_ip

def run(server_class=ThreadingHTTPServer, handler_class=ThreadedHTTPHandler, port=8000):
    """Start the threaded HTTP server."""
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)

    # Fetch and print the private IP and port
    private_ip = get_private_ip()
    print(f"{private_ip}:{port}")

    httpd.serve_forever()

if __name__ == '__main__':
    run()
