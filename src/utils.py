import time
import threading

def do_periodic(func, args, period_seconds):
    def loop():
        while True:
            if func(*args):
                print("Already valid! exiting...")
                return
            time.sleep(period_seconds)
    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
