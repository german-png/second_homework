import socket
import random
import time
from dns_request import Request
from dns_response import Response
from dns_question import Question
from dns_header import Header
from dns_cache import Cache

def send_request(ip : str, packet: Request, timeout : int  = 3) -> Request:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)

    try:
        data = packet.encode_request()
        s.sendto(data, (ip, 53))
        response_data, _ = s.recvfrom(4096)
        return Request.decode_request(response_data)

    except socket.timeout:
        return None

    except Exception:
        return None

    finally:
        s.close()


def iterative_resolve(name: str, qtype: int, cache: Cache, max_step: int = 10) -> list:
    name = name.strip('.')

    cached = cache.get_cache(name, qtype)
    if cached:
        return [cached]

    root_servers = list([
        "198.41.0.4", "199.9.14.201", "192.33.4.12", "199.7.91.13",
        "192.203.230.10", "192.5.5.241", "192.112.36.4", "198.97.190.53",
        "192.36.148.17", "192.58.128.30", "193.0.14.129", "199.7.83.42",
        "202.12.27.33"
    ])

    random.shuffle(root_servers)
    response = None

    for step in range(max_step):
        resolved = False

        for server in root_servers:
            qid = random.randint(0, 65535)
            header = Header(id=qid, flags=0, qdcount=1)
            question = Question(name, qtype)
            request = Request(header, [question])

            response = send_request(server, request)
            if response is None:
                continue

            cache.put_several(response.responses)
            cache.put_several(response.authority)
            cache.put_several(response.additional)

            if response.has_response(name, qtype):
                return response.responses

            ns_servers = []
            for ns_rec in response.authority:
                if ns_rec.type == 2:
                    ns_name = ns_rec.rdata

                    for add_rec in response.additional:
                        if(add_rec.name.lower() == ns_name.lower() and add_rec.type == 1):
                            ns_servers.append(add_rec.rdata)

            if ns_servers: 
                root_servers = ns_servers
                resolved = True
                break

        if not resolved:
            break

    if response:
        for ans in response.responses:
            if ans.type == 5:
                return iterative_resolve(ans.rdata, qtype, cache, max_step - step)

    return []