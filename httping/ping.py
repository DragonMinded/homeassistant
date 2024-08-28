import argparse
import json
import subprocess
import threading
import time

from flask import Flask, Response
from typing import Optional


def send_ping(host_or_ip: str, timeout: float = 0.5) -> bool:
    res = subprocess.run(
        ["ping", host_or_ip, "-D", "-O", "-c", "1", "-W", str(timeout)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT
    )
    return res.returncode == 0


is_responding: Optional[bool] = None


class PollingThread(threading.Thread):
    def __init__(self, host_or_ip: str, failure_threshold: int = 1, timeout: float = 0.5) -> None:
        super().__init__()
        self.host_or_ip = host_or_ip
        self.threshold = failure_threshold
        self.fail_count = 0
        self.timeout = timeout

    def run(self) -> None:
        global is_responding

        while True:
            start = time.time()
            old_is_responding = is_responding

            if send_ping(self.host_or_ip, self.timeout):
                # Succeeded, clear failure count and mark up.
                self.fail_count = 0
                is_responding = True
                print(f"Host {self.host_or_ip} reported up.")
            else:
                # Failed, increment failure count and mark down if we exceeded the
                # threshold. Default threshold has us fail after one bad ping.
                self.fail_count += 1
                if self.fail_count >= self.threshold:
                    is_responding = False
                print(f"Host {self.host_or_ip} reported down.")

            if old_is_responding != is_responding:
                print(f"Host {self.host_or_ip} marked {'up' if is_responding else 'down'}.")

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
    parser.add_argument("-c", "--count", help="Number of failures to observe before marking host down. Defaults to 1", type=int, default=1)
    args = parser.parse_args()

    polling_thread = PollingThread(args.host, args.count, args.timeout)
    polling_thread.start()

    app.config['host'] = args.host
    app.run(port=args.port, debug=args.debug)
