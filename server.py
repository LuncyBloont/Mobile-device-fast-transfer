import http.server as h_server
import qrcode
import socket
import threading
import cv2
import cgi
import os
import re
import json
import time
import sys
from urllib.parse import unquote

termOnly = True if len(sys.argv) > 1 and sys.argv[1] == '-t' else False

nets = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
nets.connect(('8.8.8.8', 80))

local_ip = nets.getsockname()[0]
ip = '0.0.0.0'
port = 8933

fileType = {
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'jfif': 'image/jpeg',
    'jpe': 'image/jpeg',
    'gif': 'image/gif',
    'ppm': 'application/x-ppm',
    'exe': 'application/msdownload',
    'mp4': 'video/mp4',
    'mp3': 'audio/mp3',
    'wav': 'audio/wav',
    'pdf': 'application/pdf'
}


class ServerCore(h_server.BaseHTTPRequestHandler):
    @staticmethod
    def check_dir():
        if not os.path.exists('share'):
            os.mkdir('share')
        if not os.path.exists('tmp'):
            os.mkdir('tmp')

    def do_GET(self):
        global fileType

        ServerCore.check_dir()

        paths = self.path.split('/')
        print(paths)

        typere = re.compile('.*\\.([^.]+)$')

        if len(paths) > 1:
            if paths[-1].find('favicon') == 0:
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.end_headers()
                with open('icon.png', 'rb') as fr:
                    ctt = fr.read()
                    self.wfile.write(ctt)
                return
            elif paths[1] == 'list':
                self.send_response(200)
                self.send_header('Content-Type', 'text/json; chartset=utf-8')
                self.end_headers()
                li = os.listdir('share')
                lid = []
                for k in li:
                    fn = k
                    fs = (os.path.getsize(os.path.join('share', fn)) * 100 // 1024) / 100
                    fd = os.path.getmtime(os.path.join('share', fn))
                    lid.append({'name': fn, 'size': fs, 'date': time.ctime(fd)})
                obj = {'list': lid}
                self.wfile.write(bytes(json.dumps(obj), 'utf-8'))
                return
            elif paths[1] == 'download':
                file = os.path.join('share', paths[2])
                if file.find('?') != -1:
                    file = file[0:file.find('?')]

                file = unquote(file, 'utf-8')

                ftype = 'application/octet-stream'
                ftype_arr = typere.match(paths[2])
                if ftype_arr:
                    typepart = ftype_arr[1]
                    for t in fileType.keys():
                        if re.match(t + '$', typepart, re.I):
                            ftype = fileType[t]
                            break

                data: bytes
                loaded: bool
                with open(file, 'rb') as f:
                    data = f.read()
                    loaded = True

                if not loaded:
                    self.send_response(404)
                    return

                self.send_response(200)
                self.send_header('Content-Type', '{}'.format(ftype))
                self.send_header('Content-Disposition', 'attachment; filename="{}"'.format(paths[2]))
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

                return
            elif paths[1] != '':
                self.send_response(404)
                return

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        with open('custom.html', 'r', encoding='utf-8') as f:
            self.wfile.write(bytes(f.read(), 'utf-8'))

    def do_POST(self):
        self.check_dir()

        form = cgi.FieldStorage(self.rfile, self.headers,
                                environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']})

        dirname = 'share' if 'share' in form else 'tmp'

        fname = form['file'].filename
        path = dirname + '/' + fname

        rgx = re.compile('(.*\\()([0-9]+)(\\)\\.[^.]+$)')
        rgx2 = re.compile('(.*\\()([0-9]+)(\\)$)')
        rgx_p = re.compile('(.*)(\\.[^.]+$)')

        while os.path.exists(path):
            r = rgx.match(path)
            r2 = rgx2.match(path)
            if r or r2:
                if r:
                    idx = int(r.group(2)) + 1
                    path = r.group(1) + str(idx) + r.group(3)
                elif r2:
                    idx = int(r2.group(2)) + 1
                    path = r2.group(1) + str(idx) + r2.group(3)
            else:
                two = rgx_p.match(path)
                if two:
                    path = two.group(1) + '(1)' + two.group(2)
                else:
                    path = path + '(1)'

        with open(path, 'wb') as fwr:
            data = form['file'].file.read()
            if len(fname) > 0:
                fwr.write(data)
                print('file {} has been save to {}'.format(fname, os.path.abspath(path)))
                print(os.path.abspath(path))
                print('file://' + os.path.abspath(path))
                print('the path and URL listed above')
            else:
                print('empty filename {}, skip.'.format(fname))

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        with open('done.html', 'r', encoding='utf-8') as f:
            self.wfile.write(bytes(f.read(), 'utf-8'))


server = h_server.HTTPServer((ip, port), ServerCore)


def run():
    global server
    server.serve_forever()


server_thread = threading.Thread(target=run)
server_thread.daemon = True
server_thread.start()

print('Use mobile device visit http://' + local_ip + ':' + str(port))

if not termOnly:
    img = qrcode.make('http://' + local_ip + ':' + str(port))
    with open('tmp.png', 'wb') as fw:
        img.save(fw)

    cvimg = cv2.imread('tmp.png')
    cv2.imshow('scan it', cvimg)
    try:
        cv2.waitKey()
    except KeyboardInterrupt:
        pass
    server.shutdown()

if termOnly:
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        server.shutdown()

print('Bye')
