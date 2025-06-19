import socket
from typing import List
import datetime
import select
from queue import Queue, ShutDown
from chat import Request_Type, Chat_Packet

DEFAULT_SERVER_ADDR = "0.0.0.0"
DEFAULT_SERVER_PORT = 33333


class Message:
    def __init__(self, username:str, date:datetime = None, body:str = ""):
        self.username = username
        self.data = date
        self.body = body
    
    def __repr__(self) -> str:
        text = f"Send by: {self.username}"
        text += text + "\n" + ("-" * len(text))
        text += self.body
        return text


class User_Session:
    def __init__(self, username:str, room_name:str, messages_read:int = 0):
        self.username = username
        self.room_name = room_name
        self.new_messages = queue()


class Room:
    def __init__(self, name:str, members:List[str] = list()):
        self.name = name
        self._members = members
        self.messages = list()
        self.subscribers = list()
    
    def add_subsriber(self, user_session:User_Session):
        self.subscribers.append(user_session.new_messages_queue)
        for msg in messages:
            user_session.new_message_queue.put(msg)

    def invoke_new_message(self, msg:Message):
        self.messages.append(msg)
        for q in self.subscribers:
            try:
                q.put(msg)
            except ShutDown as e:
                self.subscribers.remove(q)


class Server:

    def __init__(self, ip:str = DEFAULT_SERVER_ADDR, port:int = DEFAULT_SERVER_PORT, members:List[str] = list(), rooms:List[Room] = list()):
        self.ip = ip
        self.port = port
        self.members = members
        self._admins = []
        self.init_main_socket(ip, port)
        self.open_sockets = {self.main_socket: None}

    def init_main_socket(self, ip:str, port:str) -> socket.socket:
        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.main_socket.bind((ip, port))

    def accept(self):
        sock, addr = self.main_socket.accept()
        self.open_sockets.update({sock: None)})
    
    def _handle_new_connection(self, socket, request:Chat_Request):
        new_session = User_Session(*request.args)
        self.open_sockets[socket] = new_session
        print(f"New user login {new_session.args}")

    def handle_user_request(self, session):
        try:
            request = session.recv(1024)
            if request:
                print(request)
            decoded_request = Chat_Request.decode(request)
            
            if decoded_request.type == Request_Type.NEW_CONNECTION:
                self._handle_new_connection(session, decoded_request)

        except ConnectionResetError as e:
            print("Connection reseted")
            self.open_sockets.pop(session, None)

    def push_to_client(self, client_socket):
        user_session = self.open_sockets[client_socket]
        if not user_session.new_messages.isEmpty():
            try:
                msg = user_session.new_messages.get()
                client_socket.send(str(msg).encode())
            except ConnectionResetError as e:
                user_session.new_messages.shutdown()
                self.open_sockets.pop(client_socket, None)
                client_socket.close()


    def start_server(self):
        self.main_socket.listen()
        while True:
            readable, writable, _ = select.select(self.open_sockets.keys(),self.open_sockets.keys(),[])
            for session in readable:
                if session is self.main_socket:
                    self.accept()
                else:
                    self.handle_user_message(session)
            
            for client_socket in writable:
                self.push_to_client(client_socket)

        self.main_socket.close()



if __name__ == "__main__":
    server = Server(DEFAULT_SERVER_ADDR, DEFAULT_SERVER_PORT)
    server.start_server()
