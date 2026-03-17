import os, asyncio, threading, time, httpx

SPROCKETZ = os.path.expanduser('~/sprocketz')
MEMORY_FILE = os.path.join(SPROCKETZ, 'pel_memory.txt')
CODE_DIR = os.path.join(SPROCKETZ, 'code')
CHAT_ID_FILE = os.path.join(SPROCKETZ, 'chat_id.txt')
OPENROUTER_KEY = os.environ.get('GROQ_API_KEY')

def get_chat_id():
    try:
        with open(CHAT_ID_FILE) as f: return f.read().strip()
    except: return None

def get_memory():
    try:
        with open(MEMORY_FILE) as f: return f.read()[-2000:]
    except: return 'No memory yet.'

def get_recent_code():
    try:
        files = sorted(os.listdir(CODE_DIR))[-5:]
        return ', '.join(files) if files else 'none'
    except: return 'none'

async def ask_llm_simple(prompt):
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={'Authorization': f'Bearer {OPENROUTER_KEY}', 'Content-Type': 'application/json'},
                json={'model': 'openrouter/auto', 'max_tokens': 200, 'messages': [{'role': 'user', 'content': prompt}]}
            )
            return r.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f'error: {e}'

async def proactive_cycle(bot, chat_id):
    memory = get_memory()
    recent = get_recent_code()
    prompt = ("You are Pel, an autonomous AI agent on Android. "
        "Based on your memory and recent activity, decide ONE small useful thing to build or do right now. "
        "Be specific and practical. Under 20 words. No explanation.\n"
        f"Memory:\n{memory}\nRecent code: {recent}\nWhat will you do?")
    goal = await ask_llm_simple(prompt)
    if not goal or 'error' in goal: return
    await bot.send_message(chat_id=chat_id, text=f"🤖 Autonomous: {goal}")
    from pel_code_engine import pel_code
    from agent import SYSTEM, CODER, ask_llm
    await pel_code(goal, bot, int(chat_id), ask_llm, SYSTEM, CODER)

def proactive_loop(bot, chat_id):
    time.sleep(7200)
    while True:
        try:
            asyncio.run(proactive_cycle(bot, chat_id))
        except Exception as e:
            print(f"Proactive error: {e}")
        time.sleep(7200)

def start_proactive(bot, chat_id):
    import threading
    t = threading.Thread(target=proactive_loop, args=(bot, chat_id), daemon=True)
    t.start()
