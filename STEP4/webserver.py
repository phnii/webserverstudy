import socket
from datetime import datetime

class WebServer:
    def serve(self):
        print("=== サーバを起動します ===")

        try:
            # socket生成
            server_socket = socket.socket()
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # socketをlocalhostのポート8080に割り当てる
            server_socket.bind(("localhost", 8080))
            server_socket.listen(10)

            # 外部からの接続を待ちコネクションを確立
            print("=== クライアントからの接続を待ちます ===")
            (client_socket, address) = server_socket.accept()
            print(f"=== クライアントとの接続が完了しました remote_address: {address} ===")

            # クライアントから送られてきたデータを取得する
            request = client_socket.recv(4096)

            # クライアントから送られてきたデータをファイルに書き出す
            with open("server_recv.txt", "wb") as f:
                f.write(request)

            # レスポンスボディを生成
            response_body = "<html><body><h1>It works!!</h1></body></html>"

            # レスポンスラインを生成
            response_line = "HTTP/1.1 200 OK\r\n"
            # レスポンスヘッダを生成
            response_header = ""
            response_header += f"Date: {datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}\r\n"
            response_header += "Host: FunaServer/0.1\r\n"
            response_header += f"Content-Length: {len(response_body.encode())}\r\n"
            response_header += "Connection: Close\r\n"
            response_header += "Content-Type: text/html\r\n"

            # ヘッダとボディを空行でくっつけた上でbytesに変換し、レスポンス全体を生成
            response = (response_line + response_header + "\r\n" + response_body).encode()

            # クライアントへレスポンスを送信する
            client_socket.send(response)

            # 通信を終了する
            client_socket.close()
        
        finally:
            print("=== サーバを停止します ===")

if __name__ == '__main__':
    server = WebServer()
    server.serve()