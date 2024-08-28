import argparse
import json
import subprocess
import threading
import time
from flask import Flask, Response


def send_ping(host_or_ip: str, timeout: float = 0.5) -> bool:
    res = subprocess.run(
        ["ping", host_or_ip, "-D", "-O", "-c", "1", "-W", str(timeout)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT
    )
    return res.returncode == 0


is_responding: bool = False


class PollingThread(threading.Thread):
    def __init__(self, host_or_ip: str, timeout: float = 0.5) -> None:
        super().__init__()
        self.host_or_ip = host_or_ip
        self.timeout = timeout

    def run(self) -> None:
        global is_responding

        while True:
            start = time.time()

            is_responding = send_ping(self.host_or_ip, self.timeout)
            print(f"Host {self.host_or_ip} reported {'up' if is_responding else 'down'}.")

            while time.time() < (start + 1.0):
                time.sleep(0.01)


app = Flask(__name__)


@app.route("/", methods=["GET"])
def query_status() -> Response:
    return Response(
        response=json.dumps({"state": "up" if is_responding else "down", "host": app.config['host']}),
        status=200,
        mimetype="application/json",
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A simple remote host ping binary sensor over http.")
    parser.add_argument("-o", "--host", help="Host to ping. Defaults to 127.0.0.1", type=str, default="127.0.0.1")
    parser.add_argument("-p", "--port", help="Port to listen on. Defaults to 34567", type=int, default=34567)
    parser.add_argument("-d", "--debug", help="Enable debug mode. Defaults to off", action="store_true")
    parser.add_argument("-t", "--timeout", help="Seconds before timing out a ping request", type=float, default=0.5)
    args = parser.parse_args()

    polling_thread = PollingThread(args.host, args.timeout)
    polling_thread.start()

    app.config['host'] = args.host
    app.run(port=args.port, debug=args.debug)
