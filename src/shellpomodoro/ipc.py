# src/shellpomodoro/ipc.py
"""Inter-process communication module for daemon/client architecture."""

import socket
import json
import time
from typing import Optional, Dict, Any

def _connect(port: int) -> socket.socket:
    """Connect to daemon on specified port."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("localhost", port))
    return sock

def hello(sock: socket.socket, secret: str) -> bool:
    """Send authentication hello to daemon."""
    try:
        message = {"type": "hello", "secret": secret}
        data = json.dumps(message).encode() + b"\n"
        sock.send(data)
        
        response = sock.recv(1024).decode().strip()
        result = json.loads(response)
        return result.get("status") == "ok"
    except Exception:
        return False

def status(sock: socket.socket) -> Optional[Dict[str, Any]]:
    """Get current status from daemon."""
    try:
        message = {"type": "status"}
        data = json.dumps(message).encode() + b"\n"
        sock.send(data)
        
        response = sock.recv(1024).decode().strip()
        if not response:
            return None
        result = json.loads(response)
        return result if result.get("status") != "ended" else None
    except Exception:
        return None

def end_phase(sock: socket.socket) -> bool:
    """Send end phase command to daemon."""
    try:
        message = {"type": "end_phase"}
        data = json.dumps(message).encode() + b"\n"
        sock.send(data)
        return True
    except Exception:
        return False

def abort(sock: socket.socket) -> bool:
    """Send abort command to daemon."""
    try:
        message = {"type": "abort"}
        data = json.dumps(message).encode() + b"\n"
        sock.send(data)
        return True
    except Exception:
        return False
