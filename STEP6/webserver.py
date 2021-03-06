import os
import socket
import traceback
from datetime import datetime

class WebServer:
    # 実行ファイルのあるディレクトリ
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # 静的配信するファイルを置くディレクトリ
    STATIC_ROOT = os.path.join(BASE_DIR, "static")

    # 拡張子とMIME Typeの対応
    MIME_TYPES = {
        "html": "text/html",
        "css": "text/css",
        "png": "image/png",
        "jpg": "image/jpg",
        "gif": "image/gif",
    }

    def serve(self):
        print("=== サーバを起動します ===")

        try:
            # socket生成
            server_socket = socket.socket()
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # socketをlocalhostのポート8080に割り当てる
            server_socket.bind(("localhost", 8080))
            server_socket.listen(10)

            while True:
                # 外部からの接続を待ちコネクションを確立
                print("=== クライアントからの接続を待ちます ===")
                (client_socket, address) = server_socket.accept()
                print(f"=== クライアントとの接続が完了しました remote_address: {address} ===")
                try:
                    # クライアントから送られてきたデータを取得する
                    request = client_socket.recv(4096)

                    # クライアントから送られてきたデータをファイルに書き出す
                    with open("server_recv.txt", "wb") as f:
                        f.write(request)

                    # リクエスト全体を
                    # 1. リクエストライン(1行目)
                    # 2. リクエストヘッダ(2~空行)
                    # 3. リクエストボディ (空行~)
                    # にパースする
                    request_line, remain = request.split(b"\r\n", maxsplit=1)
                    request_header, request_body = remain.split(b"\r\n\r\n", maxsplit=1)

                    # リクエストラインをパースする(例 GET / HTTP/1.1)
                    method, path, http_version = request_line.decode().split(" ")
                
                    # pathの先頭の / を削除し相対パスにしておく
                    relative_path = path.lstrip("/")
                    # ファイルのパスを取得
                    static_file_path = os.path.join(self.STATIC_ROOT, relative_path)

                    try:
                        # ファイルからレスポンスボディを生成
                        with open(static_file_path, "rb") as f:
                            response_body = f.read()

                        # レスポンスラインを生成
                        response_line = "HTTP/1.1 200 OK\r\n"
                    except OSError:
                        # ファイルが見つからなかった場合は404を返す
                        response_body = b"<html><body><h1>404 Not Found</h1></body></html>"
                        response_line = "HTTP/1.1 404 Not Found\r\n"

                    # ヘッダ生成のためにContent-Typeを取得しておく
                    # pathから拡張子を取得
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

                    # ヘッダとボディを空行でくっつけた上でbytesに変換し、レスポンス全体を生成
                    response = (response_line + response_header + "\r\n").encode() + response_body

                    # クライアントへレスポンスを送信する
                    client_socket.send(response)
                except Exception:
                    # リクエスト処理中に例外が発生した場合はコンソールにエラーログを出力し
                    # 処理を続行する
                    print("=== リクエストの処理中にエラーが発生しました ===")
                    traceback.print_exc()
                finally:
                    # 例外が発生してもしなくてもcloseは行う
                    client_socket.close()

        finally:
            print("=== サーバを停止します ===")

if __name__ == '__main__':
    server = WebServer()
    server.serve()