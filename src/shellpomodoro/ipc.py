import socket, json, time


def _connect(
    port: int, host: str = "127.0.0.1", timeout: float = 2.0, max_retries: int = 20
):
    """Connect to daemon with retry logic to handle startup race conditions."""
    retry_delay = 0.05  # 50ms between retries
    total_timeout = max_retries * retry_delay

    for attempt in range(max_retries):
        try:
            s = socket.create_connection((host, port), timeout=timeout)
            s.settimeout(timeout)
            return s
        except (ConnectionRefusedError, OSError) as e:
            if attempt < max_retries - 1:  # Don't sleep on last attempt
                time.sleep(retry_delay)
                continue
            # Re-raise the last exception if all retries failed
            raise e


def hello(sock, secret: str) -> bool:
    sock.sendall(f"HELLO {secret}\n".encode("utf-8"))
    return sock.recv(1024).decode("utf-8").strip() == "OK"


def status(sock) -> dict:
    sock.sendall(b"STATUS\n")
    data = sock.recv(4096).decode("utf-8").strip()
    return json.loads(data)


def end_phase(sock) -> None:
    sock.sendall(b"END_PHASE\n")


def abort(sock) -> None:
    sock.sendall(b"ABORT\n")
