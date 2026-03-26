from http.server import BaseHTTPRequestHandler, HTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)

        print("\n=== WEBHOOK RECEIVED ===")
        print(body.decode())
        print("========================\n")

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

server = HTTPServer(('0.0.0.0', 9999), Handler)
print("Webhook server running on port 9999...")
server.serve_forever()
