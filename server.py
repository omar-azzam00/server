import os
import subprocess
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

# Bitrate variable to control video compression (kbps)
BITRATE = '500k'  # You can adjust this to reduce the video size

class VideoTranscodingHandler(SimpleHTTPRequestHandler):

    def send_response(self, code, message=None):
        super().send_response(code, message)
        self.send_header("Connection", "keep-alive")
        self.send_header("Keep-Alive", "timeout=5, max=100")

    def do_GET(self):
        file_path = self.translate_path(unquote(self.path))

        # Print the resolved file path for debugging
        print(f"Requested path: {file_path}")

        # If the request is for a directory, serve the directory listing
        if os.path.isdir(file_path):
            return super().do_GET()  # Directory listing is handled by SimpleHTTPRequestHandler

        # Serve only if the file is a video (adjust the extensions as needed)
        if os.path.isfile(file_path) and file_path.endswith(('.mp4', '.mkv', '.avi')):
            try:
                # Set the video bitrate for transcoding
                ffmpeg_command = [
                    'ffmpeg', '-i', file_path,  # Input file
                    '-b:v', BITRATE,            # Set video bitrate (compression level)
                    '-f', 'mp4',                # Force output format to mp4
                    '-movflags', 'frag_keyframe+empty_moov',  # Ensure fragmented MP4 for streaming
                    '-nostdin',                 # Disable interactive mode
                    '-v', 'error',              # Show only errors
                    'pipe:1'                    # Output to stdout (streaming)
                ]
                
                # Start ffmpeg and stream the transcoded video
                with subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE) as proc:
                    self.send_response(200)
                    self.send_header("Content-type", "video/mp4")
                    self.end_headers()

                    # Stream the transcoded video
                    while True:
                        data = proc.stdout.read(1024)
                        if not data:
                            break
                        self.wfile.write(data)

            except Exception as e:
                self.send_error(500, f"Internal server error: {e}")
        else:
            # If the file is not found or not a video, return a 404 error
            print(f"File not found or not a video: {file_path}")
            self.send_error(404, "File not found")

def run(server_class=ThreadingHTTPServer, handler_class=VideoTranscodingHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Serving on port {port}")
    httpd.serve_forever()

if __name__ == '__main__':
    # Modify the BITRATE variable to control how much compression is applied (in kbps)
    BITRATE = '350k'  # Lower bitrate results in more compression, higher quality loss
    run()
