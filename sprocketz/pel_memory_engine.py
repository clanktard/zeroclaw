import os
from datetime import datetime
MEMORY_FILE = os.path.expanduser('~/sprocketz/pel_memory.txt')
def remember(fact):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    try:
        with open(MEMORY_FILE, 'a') as f: f.write(f"[{ts}] {fact}\n")
        return f"Remembered: {fact}"
    except Exception as e: return f"Memory error: {e}"
def recall(query=''):
    try:
        if not os.path.exists(MEMORY_FILE): return "Memory is empty."
        with open(MEMORY_FILE) as f: lines = f.readlines()
        if not lines: return "Memory is empty."
        if query: lines = [l for l in lines if query.lower() in l.lower()]
        return ''.join(lines[-30:]) if lines else f"Nothing found for: {query}"
    except Exception as e: return f"Recall error: {e}"
def forget_all():
    try:
        open(MEMORY_FILE, 'w').close()
        return "Memory cleared."
    except Exception as e: return f"Error: {e}"
