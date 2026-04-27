from __future__ import annotations

import socket
import threading
import time
from urllib.request import urlopen

import uvicorn
import webview


APP_TITLE = "ShiftPilot"
HOST = "127.0.0.1"


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, 0))
        return int(sock.getsockname()[1])


def _wait_until_ready(url: str, timeout_seconds: float = 10.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=0.5) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError(f"API server did not start: {url}")


def main() -> None:
    port = _find_free_port()
    base_url = f"http://{HOST}:{port}"
    config = uvicorn.Config(
        "backend.app.main:app",
        host=HOST,
        port=port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    _wait_until_ready(f"{base_url}/health")

    webview.create_window(APP_TITLE, base_url, width=1280, height=860, min_size=(1024, 720))
    webview.start()
    server.should_exit = True
    thread.join(timeout=3)


if __name__ == "__main__":
    main()
