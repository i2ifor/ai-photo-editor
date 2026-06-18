#!/usr/bin/env python3
"""
AI图片修复工具 - 本地代理服务器
解决浏览器跨域问题，支持Replicate API
"""
import http.server
import socketserver
import json
import urllib.request
import urllib.parse
import os
import webbrowser
from pathlib import Path

PORT = 8080
DIRECTORY = Path(__file__).parent

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if self.path == '/api/replicate':
            self.handle_replicate_request()
        else:
            self.send_error(404)

    def handle_replicate_request(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)

        api_key = data.get('api_key')
        endpoint = data.get('endpoint')
        payload = data.get('payload')

        url = f'https://api.replicate.com{endpoint}'

        try:
            req_data = json.dumps(payload).encode()
            req = urllib.request.Request(url, data=req_data, method='POST')
            req.add_header('Authorization', f'Token {api_key}')
            req.add_header('Content-Type', 'application/json')

            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                self.send_json_response(result)
        except Exception as e:
            self.send_json_response({'error': str(e)}, 400)

    def do_GET(self):
        # 处理GET请求（用于轮询状态）
        if self.path.startswith('/api/replicate/'):
            self.handle_replicate_get()
        else:
            super().do_GET()

    def handle_replicate_get(self):
        # 提取prediction ID
        path_parts = self.path.split('/')
        if len(path_parts) >= 4:
            prediction_id = path_parts[3]
        else:
            self.send_error(400)
            return

        # 从查询参数获取API key
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        api_key = params.get('api_key', [None])[0]

        if not api_key:
            self.send_json_response({'error': 'Missing API key'}, 400)
            return

        url = f'https://api.replicate.com/v1/predictions/{prediction_id}'

        try:
            req = urllib.request.Request(url)
            req.add_header('Authorization', f'Token {api_key}')

            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                self.send_json_response(result)
        except Exception as e:
            self.send_json_response({'error': str(e)}, 400)

    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        print(f"🚀 AI图片修复工具已启动!")
        print(f"📱 手机访问: http://localhost:{PORT}")
        print(f"💻 电脑访问: http://localhost:{PORT}")
        print(f"\n按 Ctrl+C 停止服务器")
        webbrowser.open(f'http://localhost:{PORT}')
        httpd.serve_forever()
