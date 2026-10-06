"""Harmless demo API: echoes input as JSON; does not execute SQL or HTML."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlsplit(self.path)
        if url.path == "/health":
            payload = {"status": "ok"}
        elif url.path in ("/", "/api/search"):
            payload = {
                "message": "Request reached the demo API",
                "path": url.path,
                "parameters": parse_qs(url.query),
            }
        else:
            self.send_error(404)
            return
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()

