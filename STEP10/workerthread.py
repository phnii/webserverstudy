import os
import re
import traceback
from datetime import datetime
from socket import socket
from threading import Thread
from typing import Tuple, Optional

import views

class WorkerThread(Thread):
    # 実行ファイルのあるディレクトリ
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # 静的配信するファイルを置くディレクトリ
    STATIC_ROOT = os.path.join(BASE_DIR, "static")

    # 拡張子とMIME Typeの対応
    MIME_TYPES = {
        "html": "text/html; charset=UTF-8",
        "css": "text/css",
        "png": "image/png",
        "jpg": "image/jpg",
        "gif": "image/gif",
    }

    def __init__(self, client_socket: socket, address: Tuple[str, int]):
        super().__init__()

        self.client_socket = client_socket
        self.client_address = address

    def run(self) -> None:
        # クライアントと接続済みのsocketを受け取りリクエスト処理してレスポンスを送信する
        try:
            # クライアントから送られてきたデータをバッファから取得
            request = self.client_socket.recv(4096)

            # クライアントから送られてきたデータをファイルに書き出す
            with open("server_recv.txt", "wb") as f:
                f.write(request)

            # HTTPリクエストをパースする
            method, path, http_version, request_header, request_body = self.parse_http_request(request)

            response_body: bytes
            content_type: Optional[str]
            response_line: str
            # pathが/nowの時は、現在時刻を表示するHTMLを作成する
            if path == "/now":
                response_body, content_type, response_line = views.now()

            elif path == "/show_request":
                response_body, content_type, response_line = views.show_request(
                    method, path, http_version, request_header, request_body
                )

            elif path == "/parameters":
                response_body, content_type, response_line = views.parameters(method, request_body)
            # pathがそれ以外の時は静的ファイルからレスポンスを生成する
            else:


                try:
                    # ファイルからレスポンスボディを生成
                    response_body = self.get_static_file_content(path)

                    content_type = None

                    # レスポンスラインを生成
                    response_line = "HTTP/1.1 200 OK\r\n"
                except OSError:
                    # ファイルが見つからなかった場合は404を返す
                    response_body = b"<html><body><h1>404 Not Found</h1></body></html>"
                    content_type = "text/html; charset=UTF-8"
                    response_line = "HTTP/1.1 404 Not Found\r\n"
            
            # レスポンスヘッダを生成
            response_header = self.build_response_header(path, response_body, content_type)

            # レスポンス全体を生成
            response = (response_line + response_header + "\r\n").encode() + response_body

            # クライアントへレスポンスを送信する
            self.client_socket.send(response)
        
        except Exception:
            # リクエストを処理中に例外が発生した場合コンソールにエラーログ出力し
            # 処理を続行する
            print("=== Worker: リクエストの処理中にエラーが発生しました ===")
            traceback.print_exc()

        finally:
            # 例外が発生してもしなくても通信のcloseをする
            print(f"=== Worker: クライアントとの接続を終了します remote_address: {self.client_address} ===")
            self.client_socket.close()

    def parse_http_request(self, request: bytes) -> Tuple[str, str, str, dict, bytes]:
        # HTTPリクエストを
        # 1. method: str
        # 2. path: str
        # 3. http_version: str
        # 4. request_header: dict
        # 5. request_body: bytes
        # に分割・変換する

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
        return method, path, http_version, headers, request_body

    def get_static_file_content(self, path: str) -> bytes:
        # リクエストのpathからstaticファイルの内容を取得する
        # pathの先頭の / を削除し相対パスにしておく
        relative_path = path.lstrip("/")
        # ファイルのパスを取得
        static_file_path = os.path.join(self.STATIC_ROOT, relative_path)

        with open(static_file_path, "rb") as f:
            return f.read()

    def build_response_header(self, path: str, response_body: bytes, content_type: Optional[str]) -> str:
        # レスポンスヘッダを構築する
        # Content-Typeが指定されていない場合path
        # pathから拡張子を取得
        if content_type is None:
            if "." in path:
                ext = path.rsplit(".", maxsplit=1)[-1]
            else:
                ext = ""
            # 拡張子からMIME Typeを取得
            # 知らない対応していない拡張子の場合はoctet-streamとする
            content_type = self.MIME_TYPES.get(ext, "application/octet-stream")
        
        # レスポンスヘッダを生成
        response_header = ""
        response_header += f"Date: {datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}\r\n"
        response_header += "Host: FunaServer/0.1\r\n"
        response_header += f"Content-Length: {len(response_body)}\r\n"
        response_header += "Connection: Close\r\n"
        response_header += f"Content-Type: {content_type}\r\n"

        return response_header