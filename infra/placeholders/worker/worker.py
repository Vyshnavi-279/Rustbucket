import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

scan_count = 0


class MetricsHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        global scan_count

        if self.path == "/metrics":
            scan_count += 1

            response = f"""# HELP rustbucket_scans_started_total Number of scans started
# TYPE rustbucket_scans_started_total counter
rustbucket_scans_started_total {scan_count}
"""

            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(response.encode())

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return


def heartbeat():
    while True:
        print("Rustbucket worker heartbeat", flush=True)
        time.sleep(10)


threading.Thread(target=heartbeat, daemon=True).start()

server = HTTPServer(("0.0.0.0", 8001), MetricsHandler)

print("Rustbucket worker running on port 8001", flush=True)

server.serve_forever()