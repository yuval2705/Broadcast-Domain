import socket
from typing import List
import select
from queue import Queue
from chat import Request_Type, Chat_Request
import argparse

DEFAULT_SERVER_ADDR = "0.0.0.0"
DEFAULT_SERVER_PORT = 33333


class User_Session:
    def __init__(self, username:str = None, room_name:str = None):
        self.username = username
        self.room_name = room_name
        self.new_messages = Queue()


class Room:
    def __init__(self, name:str, members:List[str] = list(), messages:List[bytes] = list()):
        self.name = name
        self._members = members
        self.messages = messages
        self.subscribers = list()

    def add_subscriber(self, user_session:User_Session):
        self.subscribers.append(user_session.new_messages)
        for msg in self.messages:
            user_session.new_messages.put(msg)

    def invoke_new_message(self, raw_message:bytes):
        self.messages.append(raw_message)
        for q in self.subscribers:
            try:
                q.put(raw_message)
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
        self._add_test_room("kita-alef", ["yuval", "yuval2", "yuval3"], [b"blablabla", b"blablbla2", b"blblbla3"])
        self._add_test_room("kita-bet", ["yuval", "yuval2"], [b"cacacacacac", b"cacacacaca2", b"cacacaca3"])

    def _add_test_room(self, room_name:str, members:List[str], messages:List[str]):
        new_room = Room(room_name, members, messages)
        self.rooms.update({room_name : new_room})

    def init_main_socket(self, ip:str, port:str) -> socket.socket:
        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.main_socket.bind((ip, port))

    def accept(self):
        sock, addr = self.main_socket.accept()
        self.open_sockets.update({sock: None})

    def _handle_new_connection(self, client_socket, request:Chat_Request):
        
        print(self.open_sockets.get(client_socket, None))
        # If the user wants to change his room it pops the previous `User_Session` for the new one.
        self.close_user_session(self.open_sockets.get(client_socket, None))

        # The new `User_Session` object.
        new_session = User_Session(*request.args)
        self.open_sockets.update({client_socket: new_session}) 
        requested_room = self.rooms.get(new_session.room_name, None)
        if requested_room:
            requested_room.add_subscriber(new_session)
        else:
            self.close_client_connection(client_socket)

    def _handle_new_message(self, client_socket, raw_message:bytes):
        user_session = self.open_sockets.get(client_socket, None)
        if user_session is None:
            return
        requested_room = self.rooms.get(user_session.room_name, None)
        if requested_room:
            requested_room.invoke_new_message(raw_message.encode())

    def handle_user_request(self, client_socket):
        request = client_socket.recv(Chat_Request.MAX_REQUEST_SIZE)
        if not request:
            return
        decoded_request = Chat_Request.decode(request)
        req_type = decoded_request.type
        if req_type == Request_Type.NEW_CONNECTION:
            self._handle_new_connection(client_socket, decoded_request)
        if req_type == Request_Type.MESSAGE:
            self._handle_new_message(client_socket, decoded_request.args[0])
        if req_type == Request_Type.EXIT:
            self.close_client_connection(client_socket)
    
    def close_user_session(self, user_session:User_Session):
        if user_session:
            requested_room = self.rooms.get(user_session.room_name, None)
            if requested_room:
                requested_room.unsubscribe(user_session)

    def close_client_connection(self, client_socket):
        client_socket.close()
        # unsubscribe from room 
        user_session = self.open_sockets.pop(client_socket, None)
        self.close_user_session(user_session)
    
    def push_to_client(self, client_socket):
        user_session = self.open_sockets.get(client_socket, None)
        if user_session is None:
            return

        if not user_session.new_messages.empty():
            msg = user_session.new_messages.get()
            client_socket.send(msg)

    def _handle_exception(self, client_socket, excep:Exception):
        try:
            raise excep
        except ConnectionResetError as e:
            pass
        except BrokenPipeError as e:
            pass
        finally:
            print(excep)
            self.close_client_connection(client_socket)

    def start_server(self):
        self.main_socket.listen()
        while True:
            readable, writable, _ = select.select(self.open_sockets,self.open_sockets,[])
            for client_socket in readable:
                if client_socket is self.main_socket:
                    self.accept()
                else:
                    self.handle_user_request(client_socket)
            
            for client_socket in writable:
                try:
                    self.push_to_client(client_socket)
                except Exception as e:
                    self._handle_exception(client_socket, e)
 
        for sock in self.open_sockets:
            sock.close()
        self.main_socket.close()


def init_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("Chat server")
    return parser


if __name__ == "__main__":
    server = Server(DEFAULT_SERVER_ADDR, DEFAULT_SERVER_PORT)
    server.start_server()
