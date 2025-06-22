from enum import Enum

class Request_Type(bytes, Enum):
    NEW_CONNECTION = b'\x00'
    MESSAGE = b'\x01'
    TRANSFER = b'\x02'
    EXIT = b'\xFF'


class Chat_Request:
    MAX_MESSAGE_SIZE = 1024
    SPLIT_MAGIC = b'\xcc\xdd'

    def __init__(self, packet_type:Request_Type, *args):
        self.type = packet_type
        self.args = args

    def encode(self):
        msg = self.type
        for v in self.args:
            msg += Chat_Request.SPLIT_MAGIC + str(v).encode()
        return msg
    
    def new_connection_request(username:str, room:str):
        return Chat_Request(Request_Type.NEW_CONNECTION, username, room)

    def decode(raw_request):
        message_parts = raw_request.split(Chat_Request.SPLIT_MAGIC)
        packet_type = message_parts[0]
        args = message_parts[1:]
        args = [arg.decode() for arg in args]
        return Chat_Request(packet_type, *args)
