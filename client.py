import socket
from server import DEFAULT_SERVER_ADDR, DEFAULT_SERVER_PORT
from chat import Chat_Request


class Client:
    def __init__(self, username:str, room_id:str, server_ip:str, server_port:int):
        self.username = username
        self.room_id = room_id
        self.init_client_sock(server_ip, server_port)

    def init_client_sock(self, server_ip:str, server_port:int):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((server_ip, server_port))
        
    def start(self):
        new_conn_req = Chat_Request.new_connection_request("jeff", "kita alef")
        self.socket.send(new_conn_req.encode())

        while True:
            print(self.socket.recv(1024).decode())
        self.socket.close()

if __name__ == "__main__":
    c = Client("yuval", "kita alef", DEFAULT_SERVER_ADDR, DEFAULT_SERVER_PORT)
    c.start()
