import os, subprocess, threading, time, json

SPROCKETZ = os.path.expanduser('~/sprocketz')
ERROR_FILE = os.path.join(SPROCKETZ, 'last_error.txt')

def check_error():
    try:
        with open(ERROR_FILE) as f: content = f.read().strip()
        if content:
            subprocess.Popen(['python3', os.path.join(SPROCKETZ, 'pel_self_repair.py')])
    except: pass

def check_battery():
    try:
        r = subprocess.run(['termux-battery-status'], capture_output=True, text=True, timeout=10)
        d = json.loads(r.stdout)
        if d['percentage'] < 20:
            subprocess.run(['termux-notification', '--title', 'Pel', '--content', f"Battery {d['percentage']}% - plug in"])
    except: pass

def check_internet():
    try:
        r = subprocess.run(['ping', '-c', '1', '-W', '3', 'google.com'], capture_output=True, timeout=10)
        if r.returncode != 0:
            subprocess.run(['termux-notification', '--title', 'Pel', '--content', 'No internet connection'])
    except: pass

def scheduler_loop():
    while True:
        time.sleep(1800)
        check_error()
        check_battery()
        check_internet()

def start_scheduler():
    t = threading.Thread(target=scheduler_loop, daemon=True)
    t.start()
