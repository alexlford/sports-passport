#!/usr/bin/env python3
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORT = 4173


class SportsPassportHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def send_error(self, code, message=None, explain=None):
        if code == 404:
            fallback = ROOT / '404.html'
            body = fallback.read_bytes()
            self.send_response(404, message or 'Not Found')
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            if self.command != 'HEAD':
                self.wfile.write(body)
            return
        super().send_error(code, message, explain)


if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', PORT), SportsPassportHandler)
    print(f'Serving Sports Passport regression site at http://127.0.0.1:{PORT}')
    server.serve_forever()
