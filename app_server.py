import socket
import json
import time
from datetime import datetime
from urllib.parse import unquote, quote

LOG_FILE = "app_server.log"
APP_HOST, APP_PORT = "127.0.0.1", 4000
DATA_HOST, DATA_PORT = "127.0.0.1", 3000

# Cache settings
CACHE = {}
CACHE_TTL = 60  # seconds

def log_event(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")

def get_from_cache(key):
    """Check if key exists in cache and hasn't expired."""
    if key in CACHE:
        ts, data = CACHE[key]
        if time.time() - ts < CACHE_TTL:
            return data
        else:
            # Expired, remove from cache
            del CACHE[key]
    return None

def save_to_cache(key, data):
    """Save data to cache with current timestamp."""
    CACHE[key] = (time.time(), data)

def rank_listings(lst):
    return sorted(lst, key=lambda x: (int(x.get("price", 10**18)), -int(x.get("bedrooms", 0))))

def fmt_results(lst):
    out = [f"OK RESULT {len(lst)}\n"]
    for L in lst:
        out.append(
            f"{L.get('id')} | {L.get('city')} | {L.get('address')} | "
            f"${L.get('price')} | {L.get('bedrooms')} bd\n"
        )
    out.append("END\n")
    return "".join(out)

def read_json(ds_sock, cmd):
    ds_sock.sendall(cmd.encode("utf-8"))
    buf = b""
    dec = json.JSONDecoder()

    while True:
        chunk = ds_sock.recv(4096)
        if not chunk:
            return None
        buf += chunk

        try:
            text = buf.decode("utf-8", errors="ignore").lstrip()
            obj, _ = dec.raw_decode(text)
            return obj
        except Exception:
            continue

def handle_client(csock,addr, ds_sock):
    csock.sendall(b"OK app_server ready. Commands: LIST | SEARCH city=<City> max_price=<Int> | QUIT\n")

    buf = b""
    while True:
        chunk = csock.recv(1024)
        if not chunk:
            log_event(f"DISCONNECT {addr}")
            return
        buf += chunk

        while b"\n" in buf:
            line_bytes, buf = buf.split(b"\n", 1)
            line = line_bytes.decode("utf-8", errors="ignore").strip()
            log_event(f"REQUEST {addr}: {line}")
            if not line:
                continue

            parts = line.split()
            cmd = parts[0].upper()

            if cmd == "QUIT":
                log_event(f"REQUEST {addr}: QUIT")
                log_event(f"DISCONNECT {addr}")
                csock.sendall(b"OK bye\n")
                return
            elif cmd == "LIST":
                cache_key = "LIST"
                cached_data = get_from_cache(cache_key)
                
                if cached_data is not None:
                    log_event(f"CACHE HIT {addr}: {cache_key}")
                    results = rank_listings(cached_data)
                    log_event(f"RESPONSE {addr}: OK RESULT {len(results)}")
                    csock.sendall(fmt_results(results).encode("utf-8"))
                else:
                    log_event(f"CACHE MISS {addr}: {cache_key}")
                    log_event(f"FORWARD {addr}: RAW_LIST")
                    raw = read_json(ds_sock, "RAW_LIST")
                    if not isinstance(raw, list):
                        csock.sendall(b"ERROR data_server bad response\n")
                    else:
                        save_to_cache(cache_key, raw)
                        results = rank_listings(raw)
                        log_event(f"RESPONSE {addr}: OK RESULT {len(results)}")
                        csock.sendall(fmt_results(results).encode("utf-8"))

            elif cmd == "SEARCH":
                params = {}
                for p in parts[1:]:
                    if "=" in p:
                        k, v = p.split("=", 1)
                        params[k] = v
                city = unquote(params.get("city", ""))  # URL-decode city name
                try:
                    max_price = int(params.get("max_price", ""))
                except Exception:
                    csock.sendall(b"ERROR max_price must be an int\n")
                    continue

                # Create cache key from search parameters
                cache_key = f"SEARCH:{city}:{max_price}"
                cached_data = get_from_cache(cache_key)
                
                if cached_data is not None:
                    log_event(f"CACHE HIT {addr}: {cache_key}")
                    if isinstance(cached_data, dict) and "error" in cached_data:
                        csock.sendall(f"ERROR {cached_data['error']}\n".encode("utf-8"))
                    else:
                        results = rank_listings(cached_data)
                        log_event(f"RESPONSE {addr}: OK RESULT {len(results)}")
                        csock.sendall(fmt_results(results).encode("utf-8"))
                else:
                    log_event(f"CACHE MISS {addr}: {cache_key}")
                    # URL-encode city for data_server (to handle spaces)
                    ds_cmd = f"RAW_SEARCH city={quote(city)} max_price={max_price}"
                    log_event(f"FORWARD {addr}: {ds_cmd}")
                    raw = read_json(ds_sock, ds_cmd)

                    if isinstance(raw, dict) and "error" in raw:
                        save_to_cache(cache_key, raw)
                        csock.sendall(f"ERROR {raw['error']}\n".encode("utf-8"))
                    elif not isinstance(raw, list):
                        csock.sendall(b"ERROR data_server bad response\n")
                    else:
                        save_to_cache(cache_key, raw)
                        results = rank_listings(raw)
                        log_event(f"RESPONSE {addr}: OK RESULT {len(results)}")
                        csock.sendall(fmt_results(results).encode("utf-8"))

            else:
                csock.sendall(b"ERROR unknown command\n")

def main():
    # Connect to data_server
    ds_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ds_sock.connect((DATA_HOST, DATA_PORT))

    app_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    app_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    app_sock.bind((APP_HOST, APP_PORT))
    app_sock.listen()

    app_sock.settimeout(1.0)

    print(f"app_server listening on {APP_HOST}:{APP_PORT}")

    try:
        while True:
            try:
                csock, addr = app_sock.accept()
                log_event(f"CONNECT {addr}")
            except socket.timeout:
                continue

            with csock:
                print("client:", addr)
                handle_client(csock, addr, ds_sock)

    except KeyboardInterrupt:
        print("\nShutting down app_server...")

    finally:
        app_sock.close()
        ds_sock.close()

if __name__ == "__main__":
    main()
