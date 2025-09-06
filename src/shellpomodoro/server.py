from __future__ import annotations
import json, os, secrets, socket, threading, time
from typing import Dict, Tuple
from .runtime import write_runtime, remove_runtime_safely


def _beep(count: int):
    try:
        from .cli import beep  # type: ignore

        beep(count)
    except Exception:
        pass


class SessionDaemon:
    """
    Runs a Pomodoro session in the background (no rendering).
    Keeps state, advances phases by wall-clock, and beeps on transitions.
    Serves a tiny TCP control protocol on 127.0.0.1:<port>.
    """

    def __init__(
        self,
        work_min: int,
        break_min: int,
        iters: int,
        beeps: int,
        display: str,
        dot_interval: int | None,
    ):
        self.work_min = work_min
        self.break_min = break_min
        self.iters_total = iters
        self.beeps = beeps
        self.display = display
        self.dot_interval = dot_interval

        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._end_phase = threading.Event()

        # Session state
        self.phase = "Focus"  # "Focus" or "Break"
        self.iter_idx = 1  # 1..iters_total
        self.duration_s = self.work_min * 60  # Convert minutes to seconds once
        self.t0 = time.monotonic()  # start of current phase (monotonic)

    # ----- session core -----

    def _compute_timing(self) -> Tuple[float, float, float]:
        """Compute elapsed, remaining, and progress using monotonic time."""
        now = time.monotonic()
        elapsed = now - self.t0
        remaining = max(0, self.duration_s - elapsed)
        progress = min(1.0, elapsed / self.duration_s) if self.duration_s else 1.0
        return elapsed, remaining, progress

    def _advance_phase(self):
        with self._lock:
            # Beep when phase ends
            if self.beeps > 0:
                _beep(self.beeps)

            if self.phase == "Focus":
                # Go to Break, same iteration
                self.phase = "Break"
                self.duration_s = self.break_min * 60
                self.t0 = time.monotonic()
                return

            # From Break -> next Focus or end session
            if self.iter_idx >= self.iters_total:
                # Final beep at session completion
                if self.beeps > 0:
                    _beep(self.beeps)
                self._stop.set()
                return

            self.iter_idx += 1
            self.phase = "Focus"
            self.duration_s = self.work_min * 60
            self.t0 = time.monotonic()

    # ----- IPC server -----

    def _serve(self, port: int, secret: str, ready_event: threading.Event = None):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", port))
        srv.listen(8)
        srv.settimeout(0.3)

        # Signal that server is ready to accept connections
        if ready_event:
            ready_event.set()

        try:
            while not self._stop.is_set():
                try:
                    conn, _ = srv.accept()
                except socket.timeout:
                    continue
                threading.Thread(
                    target=self._handle_client, args=(conn, secret), daemon=True
                ).start()
        finally:
            try:
                srv.close()
            except Exception:
                pass

    def _handle_client(self, conn: socket.socket, secret: str):
        with conn:
            f = conn.makefile("rwb", buffering=0)
            # Handshake
            first = f.readline().decode("utf-8").strip()
            if not first.startswith("HELLO ") or first.split(" ", 1)[1] != secret:
                f.write(b"ERR\n")
                return
            f.write(b"OK\n")
            # Commands
            while True:
                line = f.readline()
                if not line:
                    return
                cmd = line.decode("utf-8").strip().upper()
                if cmd == "STATUS":
                    st = self._status_payload()
                    f.write((json.dumps(st) + "\n").encode("utf-8"))
                elif cmd == "END_PHASE":
                    self._end_phase.set()
                elif cmd == "ABORT":
                    self._stop.set()
                    return

    def _status_payload(self) -> Dict:
        with self._lock:
            elapsed, remaining, progress = self._compute_timing()
            return {
                "phase_id": f"{self.iter_idx}_{self.phase}",  # Unique per phase
                "phase_label": f"[{self.iter_idx}/{self.iters_total}] {self.phase}",
                "elapsed_s": elapsed,
                "remaining_s": remaining,
                "duration_s": self.duration_s,
                "progress": progress,
                "left": max(
                    0, int(round(remaining))
                ),  # Keep for backward compatibility
                "total": self.duration_s,  # Keep for backward compatibility
                "iter": self.iter_idx,
                "iters": self.iters_total,
                "display": self.display,
                "dot_interval": self.dot_interval,
                "done": False,
            }

    # ----- lifecycle -----

    def run(self) -> Tuple[int, str]:
        # Pick a free port and secret, start server, then write runtime file
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        secret = secrets.token_hex(16)

        # Start server thread and wait for it to be listening
        server_ready = threading.Event()
        server_thread = threading.Thread(
            target=self._serve, args=(port, secret, server_ready), daemon=True
        )
        server_thread.start()

        # Wait for server to be ready before writing runtime
        if not server_ready.wait(timeout=2.0):
            raise RuntimeError("Server failed to start within 2 seconds")

        # Only write runtime after server is confirmed listening
        write_runtime(
            {"port": port, "secret": secret, "pid": os.getpid(), "started": time.time()}
        )

        try:
            while not self._stop.is_set():
                if self._end_phase.is_set():
                    self._end_phase.clear()
                    self._advance_phase()
                    continue

                # Check if current phase is done using monotonic timing
                _, remaining, _ = self._compute_timing()
                if remaining <= 0:
                    self._advance_phase()
                    continue

                time.sleep(0.2)  # ~5 Hz tick rate for smoother updates
        finally:
            remove_runtime_safely()
        return port, secret
