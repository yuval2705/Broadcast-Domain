import socket
from server import DEFAULT_SERVER_ADDR, DEFAULT_SERVER_PORT
from chat import Chat_Request, Message_Request, Close_Request, New_Connection_Request
import select
import sys
from enum import Enum
import datetime
import argparse


class Message:
    def __init__(self, username:str, date:datetime.datetime = None, body:str = ""):
        self.username = username
        self.date = date
        self.body = body

    def __repr__(self) -> str:
        text = f"Send by: {self.username}"
        text += "\n" + ("-" * len(text)) + "\n"
        text += self.body
        return text


class Client_Command(str, Enum):
    EXIT = "exit"
    TRANSFER = "transfer"


class Client:
    COMMAND_PREFIX = "/"
    def __init__(self, username:str, room_name:str, server_ip:str, server_port:int):
        self.username = username
        self.room_name = room_name
        self.init_client_sock(server_ip, server_port)

    def init_client_sock(self, server_ip:str, server_port:int) -> None:
        """
        Inits the client socket according to the given server address and port.

        @param server_ip: The IPv4 address of the server to connect to.
        @param server_port: The port number that the server listens on.
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((server_ip, server_port))
        self.in_session = True

    def start_new_session(self, username:str=None, room_name:str=None):
        """
        Sends to the server that a new session is starting and send him the relevent information for the session.
        (like username and room_name).

        @param username: The username for the new session.
        @param room_name: The room to connect to in this new session.
        """
        if username is None:
            username = self.username
        if room_name is None:
            room_name = self.room_name

        new_conn_req = New_Connection_Request(username, room_name)
        self.socket.send(new_conn_req.encode())
    
    def _close_session(self) -> None:
        """
        Closes the current session with the server.
        """

        self.in_session = False
        close_req = Close_Request()
        self.socket.send(close_req.encode())

    def _change_room(self, new_room:str):
        """
        Creates a new session with the current username but with a new room.

        @param new_room: The room name to create the new session to.
        """
        self.start_new_session(room_name=new_room)

    def handle_command(self, cli_input:str):
        """
        Calls to the relevent functions to perfom the command.

        @param cli_input: The line that contains the command to be perfomed and its arguments.
        """
        command = cli_input[len(Client.COMMAND_PREFIX):]
        if command.startswith(Client_Command.EXIT):
            self._close_session()
        if command.startswith(Client_Command.TRANSFER):
            command_args = command.split(" ")
            if len(command_args) != 2:
                print("Invalid arguments count!")
            else:
                self._change_room(command_args[1].strip().lstrip())

    def send_message(self, cli_input:str):
        new_message = Message(username=self.username, body=cli_input)
        new_message_request = Message_Request(str(new_message))
        self.socket.send(new_message_request.encode())

    def handle_cli_input(self, cli_input:str):
        if cli_input.startswith(Client.COMMAND_PREFIX):
            self.handle_command(cli_input)
        else:
            self.send_message(cli_input)

    def handle_server_response(self):
        raw_message = self.socket.recv(Chat_Request.MAX_REQUEST_SIZE)
        decoded_message = Chat_Request.decode(raw_message)

    def start(self):
        self.start_new_session()
        while self.in_session:
            readables, _, _ = select.select([self.socket, sys.stdin], [], [])
            for r in readables:
                if r is self.socket:
                    message = self.socket.recv(Chat_Request.MAX_REQUEST_SIZE).decode()
                    if message:
                        print(message + "\n")
                else:
                    self.handle_cli_input(r.readline())

        self.socket.close()


def init_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Chat client for linux!")
    parser.add_argument("server_ip", type=str, help="The IPv4 address of the chat server")
    parser.add_argument("server_port", type=int, help="The port number of the chat server")
    parser.add_argument("username", type=str, help="The username to connect to the chat server with")
    parser.add_argument("room_name", type=str, help="The room name to connect to")
    return parser


if __name__ == "__main__":
    parser = init_argparser()
    args = parser.parse_args()

    c = Client(args.username, args.room_name, args.server_ip, args.server_port)
    c.start()
