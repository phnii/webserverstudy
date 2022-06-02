import socket


from workerthread import WorketThread

class WebServer:


    def create_server_socket(self) -> socket:
        # 通信を待ち受けるためのserver_socketを生成
        # socket生成
        server_socket = socket.socket()
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # socketをlocalhostのポート8080に割り当てる
        server_socket.bind(("localhost", 8080))
        server_socket.listen(10)
        return server_socket


    def serve(self):
        print("=== サーバを起動します ===")

        try:
            # socket生成
            server_socket = self.create_server_socket()

            while True:
                # 外部からの接続を待ちコネクションを確立
                print("=== クライアントからの接続を待ちます ===")
                (client_socket, address) = server_socket.accept()
                print(f"=== クライアントとの接続が完了しました remote_address: {address} ===")

                # クライアントを処理するスレッド作成
                thread = WorketThread(client_socket, address)
                # スレッドを実行
                thread.start()
        
        finally:
            print("=== Server: サーバを停止します ===")

if __name__ == '__main__':
    server = WebServer()
    server.serve()