import socket
import threading
import traceback

from dns_header import Header
from dns_question import Question
from dns_request import Request
from dns_cache import Cache
from dns_send_request import iterative_resolve

PORT = 53


def handle_client(data: bytes, addr, sock: socket.socket, cache: Cache):
    print(f"[DEBUG] Получено {len(data)} байт от {addr}")
    
    try:
        request = Request.decode_request(data)
        print(f"[DEBUG] Запрос распарсен: {len(request.questions)} вопросов")
    except Exception as e:
        print(f"[ERROR] Ошибка парсинга: {e}")
        traceback.print_exc()
        return

    if not request.questions:
        print("[DEBUG] Нет вопросов в запросе")
        return

    q = request.questions[0]
    name = q.qname
    qtype = q.qtype

    print(f"[QUERY] {name} type={qtype} from {addr}")

    if qtype not in (1, 28):
        print(f"[DEBUG] Неподдерживаемый тип {qtype}, отправляем NXDOMAIN")
        resp = Request(
            header=Header(id=request.header.id, flags=0x8183, qdcount=1),
            questions=[q]
        )
        sock.sendto(resp.encode_request(), addr)
        return

    print(f"[DEBUG] Запускаем iterative_resolve для {name}")
    answers = iterative_resolve(name, qtype, cache)
    print(f"[DEBUG] iterative_resolve вернул {len(answers)} ответов")

    if answers:
        resp = Request(
            header=Header(
                id=request.header.id,
                flags=0x8180,
                qdcount=1,
                ancount=len(answers)
            ),
            questions=[q],
            responses=answers
        )
        print(f"[REPLY] {name} -> {[r.rdata for r in answers]}")
    else:
        resp = Request(
            header=Header(id=request.header.id, flags=0x8183, qdcount=1),
            questions=[q]
        )
        print(f"[REPLY] {name} -> NXDOMAIN")

    sock.sendto(resp.encode_request(), addr)


def main():
    cache = Cache()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        s.bind(('0.0.0.0', PORT))
        print(f"Сервер запустился на порту {PORT}")
    except Exception as e:
        print(f"Ошибка bind на порту {PORT}: {e}")
        port = 5353
        try:
            s.bind(('0.0.0.0', port))
            print(f"Сервер запустился на порту {port}")
        except Exception as e2:
            print(f"Ошибка bind на порту {port}: {e2}")
            return

    print("Ожидание запросов")

    try:
        while True:
            data, addr = s.recvfrom(4096)
            t = threading.Thread(
                target=handle_client,
                args=(data, addr, s, cache),
                daemon=True
            )
            t.start()
    except KeyboardInterrupt:
        print(f"Статистика кэша: {cache.stats()}")
    finally:
        s.close()


if __name__ == "__main__":
    main()