import os, subprocess, httpx, asyncio

AGENT_FILE = os.path.expanduser('~/sprocketz/agent.py')
ERROR_FILE = os.path.expanduser('~/sprocketz/last_error.txt')
OPENROUTER_KEY = os.environ.get('GROQ_API_KEY')

def save_error(error):
    with open(ERROR_FILE, 'w') as f: f.write(error)

def load_error():
    try:
        with open(ERROR_FILE) as f: return f.read()
    except: return ''

async def repair(error):
    try:
        with open(AGENT_FILE) as f: source = f.read()
    except: return False
    prompt = "You are fixing a Python Telegram bot running on Android Termux. Fix ONLY the bug. Return the complete corrected Python file. No explanation. No markdown fences.\n\nERROR:\n" + error + "\n\nSOURCE:\n" + source[:6000]
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={'Authorization': f'Bearer {OPENROUTER_KEY}', 'Content-Type': 'application/json'},
            json={'model': 'openrouter/auto', 'max_tokens': 4096, 'messages': [{'role': 'user', 'content': prompt}]}
        )
        fixed = r.json()['choices'][0]['message']['content'].strip()
    if 'import' in fixed and 'def ' in fixed:
        with open(AGENT_FILE, 'w') as f: f.write(fixed)
        return True
    return False

def restart():
    subprocess.Popen(['python3', AGENT_FILE])

async def run_repair():
    error = load_error()
    if not error: return
    print(f"Repairing: {error[:100]}")
    fixed = await repair(error)
    if fixed:
        print("Fixed. Restarting.")
        save_error('')
        restart()
    else:
        print("Could not fix.")

if __name__ == '__main__':
    asyncio.run(run_repair())
