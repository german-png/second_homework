import struct

class Header:
    def __init__(self,
                 id = 0,
                 flags = 0,
                 qdcount=0,
                 ancount=0,
                 nscount=0,
                 arcount=0):
        self.id = id
        self.flags = flags
        self.qdcount = qdcount
        self.ancount = ancount
        self.nscount = nscount
        self.arcount = arcount

    def encode_header(self):
        return struct.pack("!HHHHHH", self.id, self.flags,
            self.qdcount, self.ancount, self.nscount, self.arcount)

    @staticmethod
    def decode_header(message):
        id, flags, qd, an, ns, ar = struct.unpack("!HHHHHH", message[:12])
        return Header(id, flags, qd, an, ns, ar)


        