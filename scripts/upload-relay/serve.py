# Local helper for agent uploads: serves relay.html + the queue on 127.0.0.1:8765 only.
# Usage: python serve.py <queue dir>   (see .agents/skills/agent-browser-upload)
import http.server, sys, functools, os
RELAY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'relay.html')
class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Access-Control-Allow-Headers", "*")
        super().end_headers()
    def do_GET(self):
        if self.path.startswith("/relay.html"):
            body = open(RELAY, "rb").read(); self.send_response(200); self.send_header("Content-Type", "text/html"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
        return super().do_GET()
    def do_OPTIONS(self):
        self.send_response(204); self.end_headers()
http.server.ThreadingHTTPServer(("127.0.0.1", 8765), functools.partial(H, directory=sys.argv[1])).serve_forever()
