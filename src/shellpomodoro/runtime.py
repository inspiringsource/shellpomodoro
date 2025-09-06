import json, os, tempfile, signal
from typing import Optional, Dict

RUNTIME_BASENAME = "shellpomodoro-runtime.json"


def _state_dir() -> str:
    if os.name == "nt":
        base = (
            os.environ.get("LOCALAPPDATA")
            or os.environ.get("TEMP")
            or tempfile.gettempdir()
        )
    else:
        base = (
            os.environ.get("XDG_RUNTIME_DIR")
            or os.environ.get("TMPDIR")
            or tempfile.gettempdir()
        )
    path = os.path.join(base, "shellpomodoro")
    os.makedirs(path, exist_ok=True)
    return path


def runtime_path() -> str:
    return os.path.join(_state_dir(), RUNTIME_BASENAME)


def read_runtime() -> Optional[Dict]:
    p = runtime_path()
    if not os.path.exists(p):
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def write_runtime(d: Dict) -> None:
    tmp = runtime_path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f)
    os.replace(tmp, runtime_path())


def remove_runtime_safely() -> None:
    try:
        os.remove(runtime_path())
    except FileNotFoundError:
        pass
    except Exception:
        pass


def is_process_running(pid: int) -> bool:
    """Check if a process with given PID is running (cross-platform)."""
    try:
        if os.name == "nt":
            # Windows
            import subprocess

            result = subprocess.run(
                ["tasklist", "/fi", f"PID eq {pid}"],
                capture_output=True,
                text=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return str(pid) in result.stdout
        else:
            # Unix-like (Linux, macOS)
            os.kill(pid, 0)  # Signal 0 doesn't kill, just checks if process exists
            return True
    except (OSError, ProcessLookupError):
        return False
    except Exception:
        return False


def cleanup_stale_runtime() -> bool:
    """Remove runtime file if the daemon process is dead. Returns True if cleaned up."""
    runtime = read_runtime()
    if not runtime:
        return False

    pid = runtime.get("pid")
    if not pid:
        remove_runtime_safely()
        return True

    if not is_process_running(pid):
        remove_runtime_safely()
        return True

    return False
