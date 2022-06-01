import socket
from typing import final

class TCPClient:
    def request(self):
        print("=== クライアントを起動します ===")

        try:
            #socket生成
            client_socket = socket.socket()
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # サーバと接続する
            print("=== サーバと接続します ===")
            # ローカルマシンのポート80のapachサーバに向けて接続
            client_socket.connect(("127.0.0.1", 80))
            # 接続の確立時にクライアント側のポートはsocketライブラリによって自動的に割り当てられる
            print("=== サーバとの接続が完了しました ===")

            # サーバに送信するリクエストをファイルから取得
            with open("client_send.txt", "rb") as f: # バイト列で書き込む
                request = f.read()

            # サーバへリクエストを送信する
            client_socket.send(request) #send()の引数はバイト列である必要

            # サーバからのレスポンスを待ち取得する
                # recvメソッドは実行時点でバッファにデータが溜まっていたら即座にそのデータを返す
                # バッファが空であればデータが来るまで待機
            response = client_socket.recv(4096)

            # レスポンスの内容をファイルに書き出す
            with open("client_recv.txt", "wb") as f:
                f.write(response)

            # 通信を終了する
            client_socket.close()

        finally:
            print("=== クライアントを停止します ===")

if __name__ == '__main__':
    client = TCPClient()
    client.request()