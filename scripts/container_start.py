"""Single-user container: shared loopback for the existing UI proxy and API.

Only Docker publishes the documented loopback ports. No provider is started here.
"""
import signal
import subprocess
import sys
import time


def main():
    children = []
    stopping = False

    def stop(*_):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        children.append(subprocess.Popen([sys.executable, '-m', 'uvicorn', 'lastcopy.api:app', '--host', '0.0.0.0', '--port', '8000']))
        children.append(subprocess.Popen(['node', 'node_modules/next/dist/bin/next', 'start', 'web', '--hostname', '0.0.0.0', '--port', '3000']))
        while not stopping and all(p.poll() is None for p in children):
            time.sleep(.2)
        return 0 if stopping else next((p.returncode for p in children if p.returncode is not None), 1)
    finally:
        for p in children:
            if p.poll() is None:
                p.terminate()
        for p in children:
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait()


if __name__ == '__main__':
    raise SystemExit(main())
