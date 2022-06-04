import re
import traceback
from datetime import datetime
from re import Match
from socket import socket
from threading import Thread
from typing import Tuple, Optional
from fango.urls.resolver import URLResolver

from fango.http.request import HTTPRequest
from fango.http.response import HTTPResponse

class Worker(Thread):

    # 拡張子とMIME Typeの対応
    MIME_TYPES = {
        "html": "text/html; charset=UTF-8",
        "css": "text/css",
        "png": "image/png",
        "jpg": "image/jpg",
        "gif": "image/gif",
    }

    # ステータスコードとステータスラインの対応
    STATUS_LINES = {
        200: "200 OK",
        404: "404 Not Found",
        405: "405 Method Not Allowed",
    }

    def __init__(self, client_socket: socket, address: Tuple[str, int]):
        super().__init__()

        self.client_socket = client_socket
        self.client_address = address

    def run(self) -> None:
        # クライアントと接続済みのsocketを受け取りリクエスト処理してレスポンスを送信する
        try:
            # クライアントから送られてきたデータをバッファから取得
            request_bytes = self.client_socket.recv(4096)

            # クライアントから送られてきたデータをファイルに書き出す
            with open("server_recv.txt", "wb") as f:
                f.write(request_bytes)

            # HTTPリクエストをパースする
            request = self.parse_http_request(request_bytes)

            view = URLResolver().resolve(request)

            response = view(request)

            if isinstance(response.body, str):
                response.body = response.body.encode()

            response_line = self.build_response_line(response)

            response_header = self.build_response_header(response, request)

            response_bytes = (response_line + response_header + "\r\n").encode() + response.body

            self.client_socket.send(response_bytes)


        except Exception:
            # リクエストを処理中に例外が発生した場合コンソールにエラーログ出力し
            # 処理を続行する
            print("=== Worker: リクエストの処理中にエラーが発生しました ===")
            traceback.print_exc()

        finally:
            # 例外が発生してもしなくても通信のcloseをする
            print(f"=== Worker: クライアントとの接続を終了します remote_address: {self.client_address} ===")
            self.client_socket.close()

    def parse_http_request(self, request: bytes) -> HTTPRequest:
        # リクエスト全体を
        # 1. リクエストライン(1行目)
        # 2. リクエストヘッダ(2~空行)
        # 3. リクエストボディ (空行~)
        # にパースする
        request_line, remain = request.split(b"\r\n", maxsplit=1)
        request_header, request_body = remain.split(b"\r\n\r\n", maxsplit=1)

        # リクエストラインをパースする(例 GET / HTTP/1.1)
        method, path, http_version = request_line.decode().split(" ")

        # リクエストヘッダを辞書にパースする
        headers = {}
        for header_row in request_header.decode().split("\r\n"):
            key, value = re.split(r": *", header_row, maxsplit=1)
            headers[key] = value
        return HTTPRequest(method=method, path=path, http_version=http_version, headers=headers, body=request_body)


    def build_response_line(self, response: HTTPResponse) -> str:
        # レスポンスラインを構築する
        status_line = self.STATUS_LINES[response.status_code]
        return f"HTTP/1.1 {status_line}"

    def build_response_header(self, response: HTTPResponse, request: HTTPRequest) -> str:
        # レスポンスヘッダを構築する
        # Content-Typeが指定されていない場合path
        # pathから拡張子を取得
        if response.content_type is None:
            if "." in request.path:
                ext = request.path.rsplit(".", maxsplit=1)[-1]
                # 拡張子からMIME Typeを取得
                # 知らない対応していない拡張子の場合はoctet-streamとする
                response.content_type = self.MIME_TYPES.get(ext, "application/octet-stream")
            else:
                # pathに拡張子がない場合はhtml扱いとする
                response.content_type = "text/html; charset=UTF-8"

        
        # レスポンスヘッダを生成
        response_header = ""
        response_header += f"Date: {datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}\r\n"
        response_header += "Host: FunaServer/0.1\r\n"
        response_header += f"Content-Length: {len(response.body)}\r\n"
        response_header += "Connection: Close\r\n"
        response_header += f"Content-Type: {response.content_type}\r\n"

        return response_header

    def url_match(self, url_pattern: str, path: str) -> Optional[Match]:
        # URLパターンを正規表現パターンに変化する
        # '/user/<user_id>/profile' => '/user/(?P<user_id>[^/]+)/profile'
        re_pattern = re.sub(r"<(.+?)>", r"(?P<\1>[^/]+)", url_pattern)
        return re.match(re_pattern, path)