import time
import threading

def do_periodic(func, period_seconds):
    def loop():
        while True:
            func()
            time.sleep(period_seconds)
    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
