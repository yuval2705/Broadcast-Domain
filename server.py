import socket
from typing import List
import datetime
import select
from queue import Queue
from chat import Request_Type, Chat_Request

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
    def __init__(self, username:str = None, room_name:str = None, messages_read:int = 0, **kwargs):
        self.username = username
        self.room_name = room_name
        self.new_messages = Queue()
    

class Room:
    def __init__(self, name:str, members:List[str] = list(), messages:List[str] = list()):
        self.name = name
        self._members = members
        self.messages = messages
        self.subscribers = list()
    
    def add_subscriber(self, user_session:User_Session):
        self.subscribers.append(user_session.new_messages)
        for msg in self.messages:
            user_session.new_messages.put(msg)

    def invoke_new_message(self, msg:Message):
        self.messages.append(msg)
        for q in self.subscribers:
            try:
                q.put(msg)
            except Exception as e:
                self.subscribers.remove(q)

    def unsubscribe(self, user_session:User_Session):
        if user_session.new_messages in self.subscribers:
            self.subscribers.remove(user_session.new_messages)

class Server:

    def __init__(self, ip:str = DEFAULT_SERVER_ADDR, port:int = DEFAULT_SERVER_PORT, members:List[str] = list(), rooms:List[Room] = list()):
        self.ip = ip
        self.port = port
        self.members = members
        self._admins = []
        self.init_main_socket(ip, port)
        self.open_sockets = {self.main_socket: None}
        self.rooms = dict()
        # Tests
        self._add_test()

    def _add_test(self):
        self._add_test_room("kita alef", ["yuval", "yuval2", "yuval3"], ["blablabla", "blablbla2", "blblbla3"])

    def _add_test_room(self, room_name:str, members:List[str], messages:List[str]):
        new_room = Room(room_name, members, messages)
        self.rooms.update({room_name : new_room})


    def init_main_socket(self, ip:str, port:str) -> socket.socket:
        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.main_socket.bind((ip, port))

    def accept(self):
        sock, addr = self.main_socket.accept()
        print(sock)
        self.open_sockets.update({sock: None})

    def _handle_new_connection(self, socket, request:Chat_Request):
        new_session = User_Session(*request.args)
        print(socket)
        print(f"New user login {new_session.username} {new_session.room_name}")
        self.open_sockets.update({socket: new_session}) 
        requested_room = self.rooms.get(new_session.room_name, None)
        if requested_room:
            print(new_session)
            requested_room.add_subscriber(new_session)
        else:
            self.remove_connection(socket)

    def handle_user_request(self, socket):
        try:
            request = socket.recv(1024)
            if not request:
                return
            print(request)
            decoded_request = Chat_Request.decode(request)
            if decoded_request.type == Request_Type.NEW_CONNECTION:
                self._handle_new_connection(socket, decoded_request)

        except ConnectionResetError as e:
            print("Connection reseted")
            self.remove_connection(socket)

    def remove_connection(self, socket):
        socket.close()
        # unsubscribe from room 
        user_session = self.open_sockets.pop(socket, None)
        if user_session:
            requested_room = self.rooms.get(user_session.room_name, None)
            if requested_room:
                requested_room.unsubscribe(user_session)

    def push_to_client(self, client_socket):
        user_session = self.open_sockets.get(client_socket, None)
        if user_session is None:
            return

        if not user_session.new_messages.empty():
            try:
                msg = user_session.new_messages.get()
                client_socket.send(str(msg).encode())
            except ConnectionResetError as e:
                self.remove_connection(client_socket, None)

    def start_server(self):
        self.main_socket.listen()
        while True:
            readable, writable, _ = select.select(self.open_sockets,self.open_sockets,[])
            for socket in readable:
                if socket is self.main_socket:
                    self.accept()
                else:
                    self.handle_user_request(socket)
            
            for client_socket in writable:
                self.push_to_client(client_socket)

        self.main_socket.close()



if __name__ == "__main__":
    server = Server(DEFAULT_SERVER_ADDR, DEFAULT_SERVER_PORT)
    server.start_server()
