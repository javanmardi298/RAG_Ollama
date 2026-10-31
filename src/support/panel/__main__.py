"""Start the control panel:  python -m support.panel  [--port 8765] [--no-browser]"""
from __future__ import annotations

import argparse
import threading
import webbrowser

from . import envfile, runner


def main() -> None:
    p = argparse.ArgumentParser(description="Support Agent control panel")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--no-browser", action="store_true")
    a = p.parse_args()

    import uvicorn

    envfile.load_into_environ()
    runner.reconcile()
    url = f"http://127.0.0.1:{a.port}"
    print(f"Control panel: {url}   (Ctrl+C to stop; running jobs keep going)")
    if not a.no_browser:
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    uvicorn.run("support.panel.web:app", host="127.0.0.1", port=a.port, log_level="warning")


if __name__ == "__main__":
    main()
