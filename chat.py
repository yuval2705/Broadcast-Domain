from enum import Enum

class Request_Type(bytes, Enum):
    NEW_CONNECTION = b'\x00'
    MESSAGE = b'\x01'
    TRANSFER = b'\x02'
    EXIT = b'\xFF'


class Chat_Request:
    MAX_REQUEST_SIZE = 1024
    SPLIT_MAGIC = b'\xcc\xdd'

    def __init__(self, packet_type:Request_Type, *args):
        self.type = packet_type
        self.args = args

    def encode(self):
        msg = self.type
        for v in self.args:
            msg += Chat_Request.SPLIT_MAGIC + v
        return msg
    
    def decode(raw_request):
        message_parts = raw_request.split(Chat_Request.SPLIT_MAGIC)
        packet_type = message_parts[0]
        args = message_parts[1:]
        args = [arg.decode() for arg in args]
        return Chat_Request(packet_type, *args)


class New_Connection_Request(Chat_Request):
    def __init__(self, username:str, room:str):
        super().__init__(Request_Type.NEW_CONNECTION, username.encode(), room.encode())


class Message_Request(Chat_Request):
    def __init__(self, message:str):
        super().__init__(Request_Type.MESSAGE, message.encode())


class Close_Request(Chat_Request):
    def __init__(self):
        super().__init__(Request_Type.EXIT)
