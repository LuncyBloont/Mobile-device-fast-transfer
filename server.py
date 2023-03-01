import http.server as Server
import qrcode
import socket
import cv2
import threading
import cgi
import os
import re

nets = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
nets.connect(('8.8.8.8', 80))

local_ip = nets.getsockname()[0]
ip = '0.0.0.0'
port = 8933

class ServerCore(Server.BaseHTTPRequestHandler):
    def do_GET(self):
        print(self.request)
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        with open('custom.html', 'r', encoding='utf-8') as f:
            self.wfile.write(bytes(f.read(), 'utf-8'))
    
    def do_POST(self):
        form = cgi.FieldStorage(self.rfile, self.headers, environ={ 'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type'] })
        
        path = 'tmp/' + form['file'].filename

        rgx = re.compile('(.*\()([0-9]+)(\)\.[^.]+$)')
        rgx2 = re.compile('(.*\()([0-9]+)(\)$)')
        rgxP = re.compile('(.*)(\.[^.]+$)')

        while os.path.exists(path):
            r = rgx.match(path)
            r2 = rgx2.match(path)
            if r or r2:
                if r:
                    id = int(r.group(2)) + 1
                    path = r.group(1) + str(id) + r.group(3)
                elif r2:
                    id = int(r2.group(2)) + 1
                    path = r2.group(1) + str(id) + r2.group(3)
            else:
                two = rgxP.match(path)
                if two:
                    path = two.group(1) + '(1)' + two.group(2)
                else:
                    path = path + '(1)'

        with open(path, 'wb') as fw:
            data = form['file'].file.read()
            fw.write(data)
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        with open('done.html', 'r', encoding='utf-8') as f:
            self.wfile.write(bytes(f.read(), 'utf-8'))

        
server = Server.HTTPServer((ip, port), ServerCore)

def run():
    global server
    server.serve_forever()

t = threading.Thread(target=run)
t.start()

img = qrcode.make('http://' + local_ip + ':' + str(port))
print('Use mobile device visit http://' + local_ip + ':' + str(port))
with open('tmp.png', 'wb') as fw:
    img.save(fw)

cvimg = cv2.imread('tmp.png')
cv2.imshow('scan it', cvimg)
cv2.waitKey()

server.shutdown()
print('Bye')
