import socket
import time
from multiprocessing import Process, Manager
import subprocess

# save server address and port
HOST = "128.171.80.243"
PORT = 915

def log_shutter_status(value):
    path = "/i/cloudcam/camera/shutter"
    comment = "Sun Shutter Status"
    try:
        subprocess.run([
            "ssPut", 
            f"NAME={path}", 
            f"VALUE={value}", 
            f"COMMENT={comment}"], 
            check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error logging shutter status (exit {e.returncode}): {e}")
    except Exception as e:
        print(f"Error logging shutter status: {e}")

def raw_set_gpio(state):
    with socket.create_connection((HOST, PORT)) as s:
        s.sendall((f'shutter {state}').encode() + b'\n')
        raw_resp = s.recv(1024).decode()

def set_worker(state, result_list):
    try:
        result_list.append(raw_set_gpio(state))
    except Exception as e:
        result_list.append(e)

def set_with_timeout(state, timeout=20):
    mgr   = Manager()
    result = mgr.list()

    while True:
        p = Process(target=set_worker, args=(state, result))
        p.start()
        p.join(timeout)

        if p.is_alive():
            p.terminate()
            p.join()
            print(f"raw_set_gpio took too long (>{timeout}s), retrying...")
            log_shutter_status("Timeout, retrying...")
            continue

        val = result[0] if result else None
        if isinstance(val, Exception):
            print(f"raw_set_gpio raised an exception: {val!r}, retrying...")
            log_shutter_status("Exception, retrying...")
            result[:] = []  # clear
            time.sleep(10)
            continue

        return val  # success path

def set_gpio(state):
    log_shutter_status(state)
    set_with_timeout(state, timeout=20)