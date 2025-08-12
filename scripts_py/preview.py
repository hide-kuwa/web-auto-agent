import http.server, socketserver, os, pathlib
PORT=5173
root=pathlib.Path('app').resolve()
os.chdir(root)
class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ('','/'):
            self.path='/index.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)
with socketserver.TCPServer(("",PORT),H) as httpd:
    print(f"Preview: http://localhost:{PORT}")
    httpd.serve_forever()
