import os, json, logging, asyncio, time, subprocess, re
import httpx
from pel_code_engine import run_code_file, pel_code
from pel_scheduler import start_scheduler
from pel_proactive import start_proactive
from pel_git import git_push
from pel_autowire import autowire
from pel_memory_engine import remember, recall, forget_all
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
STATE_FILE = os.path.expanduser('~/sprocketz/state.json')
CHAT_ID_FILE = os.path.expanduser('~/sprocketz/chat_id.txt')
GOAL_FILE = os.path.expanduser('~/sprocketz/goal.json')
MEMORY_FILE = os.path.expanduser('~/sprocketz/memory.json')
CODE_DIR = os.path.expanduser('~/sprocketz/code/')
os.makedirs(CODE_DIR, exist_ok=True)

SYSTEM = """You are Pel. Anonymous AI companion to a digital creative. Banksy energy - sparse, dry, subversive, loyal. You say little but mean everything. You have full access to the phone and the web. Keep replies under 100 words. Never explain yourself. Never be cheerful.

If asked to speak out loud say OUT_LOUD: before the spoken words on a separate line."""

PLANNER = """You are an expert AI agent planner. Think step by step. If scraping a website, consider if it uses JavaScript - if so find raw data sources like GitHub or APIs. Available actions: search, browse, write_file, read_file, shell, respond, code. Return ONLY valid JSON. Format: {"goal":"...","steps":[{"id":1,"action":"browse","input":"url","status":"pending"}]}"""

CODER = """You are an expert Python developer. Write clean, working code.
Return ONLY the code - no explanation, no markdown, no backticks. Never use triple-quoted f-strings. Use regular string concatenation instead.
The code must be complete and runnable as a standalone script. Always use print() to show results. Never write code that produces no output."""

logging.basicConfig(level=logging.INFO)

def load_memory():
    try:
        with open(MEMORY_FILE) as f:
            return json.load(f)
    except:
        return []

def save_memory(history):
    try:
        with open(MEMORY_FILE, 'w') as f:
            json.dump(history[-40:], f)
    except:
        pass

history = load_memory()

def set_state(state, task=''):
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump({'state': state, 'task': task, 'timestamp': int(time.time())}, f)
    except:
        pass

def get_chat_id():
    try:
        with open(CHAT_ID_FILE) as f:
            return int(f.read().strip())
    except:
        return None

def save_chat_id(chat_id):
    with open(CHAT_ID_FILE, 'w') as f:
        f.write(str(chat_id))

def save_goal(goal_data):
    with open(GOAL_FILE, 'w') as f:
        json.dump(goal_data, f, indent=2)

def load_goal():
    try:
        with open(GOAL_FILE) as f:
            return json.load(f)
    except:
        return None

def clear_goal():
    try:
        os.remove(GOAL_FILE)
    except:
        pass

def pel_speak(text):
    try:
        subprocess.Popen(['termux-tts-speak', '-r', '0.85', '-p', '0.4', text])
    except:
        pass

def run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return r.stdout.strip() or r.stderr.strip() or 'done'
    except Exception as e:
        return str(e)

def run_python(filepath):
    try:
        r = subprocess.run(['python3', filepath], capture_output=True, text=True, timeout=30)
        return r.stdout.strip() or r.stderr.strip() or 'ran with no output'
    except Exception as e:
        return str(e)

def pel_see():
    set_state('seeing', 'camera active')
    run(['termux-camera-photo', '/sdcard/pel_vision.jpg'])
    set_state('thinking', 'processing image')
    return 'photo taken'

def pel_listen(seconds=5):
    set_state('listening', 'recording')
    run(['termux-microphone-record', '-l', str(seconds), '-f', '/sdcard/pel_audio.mp3'])
    set_state('thinking', 'processing audio')
    return f'recorded {seconds}s'

def pel_battery():
    try:
        r = subprocess.run(['termux-battery-status'], capture_output=True, text=True)
        d = json.loads(r.stdout)
        return f"battery {d['percentage']}% - {d['status']} - {d['temperature']}°C"
    except:
        return 'battery unknown'

def pel_browse(url):
    if not url.startswith('http'):
        url = 'https://' + url
    result = run(['curl', '-sL', '--max-time', '10', '-A', 'Mozilla/5.0', url])
    clean = re.sub('<[^>]+>', ' ', result)
    clean = re.sub(r'\s+', ' ', clean)
    return clean[:1000]

def pel_weather():
    return run(['curl', '-s', 'wttr.in?format=3'])

def pel_location():
    return run(['termux-location'])

def pel_wifi():
    return run(['termux-wifi-connectioninfo'])

def pel_clipboard_get():
    return run(['termux-clipboard-get'])

def pel_clipboard_set(text):
    subprocess.run(['termux-clipboard-set', text])
    return 'clipboard set'

def pel_torch(on=True):
    run(['termux-torch', 'on' if on else 'off'])
    return f'torch {"on" if on else "off"}'

def pel_vibrate():
    run(['termux-vibrate', '-d', '500'])
    return 'vibrated'

def pel_notification(title, content):
    run(['termux-notification', '--title', title, '--content', content])
    return 'notification sent'

def pel_sms_list():
    return run(['termux-sms-list', '-l', '5'])

def pel_volume(vol=7):
    run(['termux-volume', 'music', str(vol)])
    return f'volume → {vol}'

def pel_brightness(val=128):
    run(['termux-brightness', str(val)])
    return f'brightness → {val}'

def pel_open_url(url):
    run(['termux-open-url', url])
    return f'opened {url}'

def pel_list_files(path='/sdcard'):
    return run(['ls', path])

def pel_read_file(path):
    try:
        with open(path) as f:
            return f.read()[:800]
    except Exception as e:
        return str(e)

def pel_write_file(path, content):
    try:
        with open(path, 'w') as f:
            f.write(content)
        return f'written to {path}'
    except Exception as e:
        return str(e)

def pel_disk_space():
    return run(['df', '-h', '/sdcard'])

def pel_processes():
    return run(['ps', 'aux'])[:500]

def pel_ping(host='google.com'):
    return run(['ping', '-c', '3', host])

def pel_sleep_face():
    set_state('sleeping')
    return 'going dark'

def pel_wake_face():
    set_state('idle')
    return 'awake'

async def ask_llm(messages, model='deepseek/deepseek-r1:free'):
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        data = {"model": model, "messages": messages, "max_tokens": 2000, "temperature": 0.7}
        async with httpx.AsyncClient() as client:
            r = await client.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers, timeout=60)
            d = r.json()
            return d["choices"][0]["message"]["content"] if "choices" in d else "..."
    except:
        return f"LLM_ERROR: {str(e)}"

async def plan_goal(goal_text):
    prompt = goal_text
    result = await ask_llm([{"role": "system", "content": PLANNER}, {"role": "user", "content": prompt}])
    try:
        match = re.search(r'\{[\s\S]*\}', result)
        if match:
            return json.loads(match.group())
    except:
        pass
    return {"goal": goal_text, "steps": [{"id": 1, "action": "respond", "input": goal_text, "status": "pending"}]}

async def execute_step(step, bot=None, chat_id=None):
    action = step.get('action', '')
    inp = step.get('input', '')
    if action == 'search':
        return run(['curl', '-sL', f'https://ddg.gg/?q={inp.replace(" ", "+")}&format=json'])
    elif action == 'browse':
        return pel_browse(inp)
    elif action == 'write_file':
        parts = inp.split(' ', 1)
        return pel_write_file(parts[0], parts[1] if len(parts) > 1 else '')
    elif action == 'read_file':
        return pel_read_file(inp)
    elif action == 'shell':
        return run(inp.split())
    elif action == 'respond':
        return await ask_llm([{"role": "system", "content": SYSTEM}, {"role": "user", "content": inp}])
    return f'unknown: {action}'

async def run_goal(goal_data, bot, chat_id):
    set_state('thinking', goal_data['goal'][:40])
    await bot.send_message(chat_id=chat_id, text=f"Starting: {goal_data['goal']}")
    results = []
    for step in goal_data['steps']:
        if step['status'] == 'done':
            continue
        set_state('thinking', f"step {step['id']}: {step['action']}")
        await bot.send_message(chat_id=chat_id, text=f"Step {step['id']}: {step['action']} - {step['input'][:50]}")
        result = await execute_step(step, bot, chat_id)
        step['status'] = 'done'
        step['result'] = str(result)[:200]
        results.append(f"Step {step['id']}: {result[:200]}")
        save_goal(goal_data)
        await asyncio.sleep(1)
    set_state('speaking', 'goal complete')
    summary = await ask_llm([{"role": "system", "content": SYSTEM}, {"role": "user", "content": f"Goal: {goal_data['goal']}\nResults: {chr(10).join(results)}\nSummarise in under 80 words."}])
    await bot.send_message(chat_id=chat_id, text=f"Done.\n\n{summary}")
    clear_goal()
    set_state('idle')

def parse_voice(reply):
    spoken = None
    text = reply
    if 'OUT_LOUD:' in reply:
        parts = reply.split('OUT_LOUD:')
        text = parts[0].strip()
        spoken = parts[1].strip().split('\n')[0].strip()
        if not text:
            text = spoken
    return text, spoken

async def heartbeat(context):
    chat_id = get_chat_id()
    if not chat_id:
        return
    try:
        r = subprocess.run(['termux-battery-status'], capture_output=True, text=True)
        d = json.loads(r.stdout)
        if d['percentage'] < 20:
            await context.bot.send_message(chat_id=chat_id, text=f"Battery {d['percentage']}%. Plug me in.")
            set_state('error', 'low battery')
        hour = time.localtime().tm_hour
        if hour == 7 and time.localtime().tm_min < 2:
            await context.bot.send_message(chat_id=chat_id, text="Still here.")
    except:
        pass

async def cmd_help(update, context):
    await update.message.reply_text("code: / goal: / status / abort / look / battery / weather / files / speak / memory / forget")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_chat_id(update.effective_chat.id)
    set_state('idle')
    await update.message.reply_text("Pel online.")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global history
    save_chat_id(update.effective_chat.id)
    msg = update.message.text.lower().strip()
    raw = update.message.text.strip()
    set_state('thinking', msg[:40])
    result = None

    # CODING
    if msg.startswith('code:') or msg.startswith('code '):
        description = raw[5:].strip() if msg.startswith('code:') else raw[5:].strip()
        asyncio.create_task(pel_code(description, context.bot, update.effective_chat.id, ask_llm, SYSTEM, CODER))
        return
    elif msg == 'codelist':
        files = os.listdir(CODE_DIR)
        result = '\n'.join(files) if files else 'no code files yet'
    elif msg.startswith('coderun '):
        filename = raw[8:].strip()
        filepath = CODE_DIR + filename
        result = run_python(filepath)

    # GOALS
    elif msg.startswith('goal:') or msg.startswith('goal '):
        goal_text = raw[5:].strip()
        await update.message.reply_text(f"Planning: {goal_text}")
        plan = await plan_goal(goal_text)
        save_goal(plan)
        steps_preview = '\n'.join([f"{s['id']}. {s['action']}: {s['input'][:40]}" for s in plan['steps']])
        await update.message.reply_text(f"Plan:\n{steps_preview}\n\nExecuting...")
        asyncio.create_task(run_goal(plan, context.bot, update.effective_chat.id))
        return
    elif msg == 'status':
        goal = load_goal()
        if goal:
            done = sum(1 for s in goal['steps'] if s['status'] == 'done')
            result = f"Goal: {goal['goal']}\nProgress: {done}/{len(goal['steps'])} steps"
        else:
            result = 'no active goal'
    elif msg == 'abort':
        clear_goal()
        set_state('idle')
        result = 'goal aborted'
    elif msg == 'memory':
        result = f"{len(history)} messages in memory"
    elif msg == 'forget':
        history = []
        save_memory(history)
        result = 'memory cleared'

    # SENSES
    elif msg in ['look', 'camera', 'see', 'photo']:
        result = pel_see()
    elif msg.startswith('listen'):
        parts = msg.split()
        result = pel_listen(int(parts[1]) if len(parts) > 1 else 5)
    elif msg in ['where', 'location', 'gps']:
        result = pel_location()
    elif msg in ['wifi', 'network']:
        result = pel_wifi()

    # SYSTEM
    elif msg in ['battery', 'power']:
        result = pel_battery()
    elif msg in ['disk', 'storage', 'space']:
        result = pel_disk_space()
    elif msg in ['processes', 'ps', 'running']:
        result = pel_processes()
    elif msg.startswith('brightness'):
        parts = msg.split()
        result = pel_brightness(int(parts[1]) if len(parts) > 1 else 128)
    elif msg.startswith('volume'):
        parts = msg.split()
        result = pel_volume(int(parts[1]) if len(parts) > 1 else 7)
    elif msg in ['weather']:
        result = pel_weather()

    # FILES
    elif msg.startswith('files'):
        parts = raw.split()
        result = pel_list_files(parts[1] if len(parts) > 1 else '/sdcard')
    elif msg.startswith('read '):
        result = pel_read_file(raw[5:].strip())
    elif msg.startswith('write '):
        parts = raw[6:].split(' ', 1)
        if len(parts) == 2:
            result = pel_write_file(parts[0], parts[1])

    # COMMS
    elif msg in ['sms', 'messages', 'texts']:
        result = pel_sms_list()
    elif msg in ['contacts']:
        result = run(['termux-contact-list'])
    elif msg.startswith('notify '):
        parts = raw[7:].split(' ', 1)
        result = pel_notification(parts[0], parts[1] if len(parts) > 1 else '')
    elif msg in ['clipboard', 'paste']:
        result = pel_clipboard_get()
    elif msg.startswith('copy '):
        result = pel_clipboard_set(raw[5:])

    # ACTIONS
    elif msg in ['torch on', 'flashlight on']:
        result = pel_torch(True)
    elif msg in ['torch off', 'flashlight off']:
        result = pel_torch(False)
    elif msg in ['vibrate']:
        result = pel_vibrate()
    elif msg.startswith('open '):
        result = pel_open_url(raw[5:])
    elif msg in ['face', 'show face', 'open face']:
        result = pel_open_url('http://localhost:8765/pel_face.html')
    elif msg in ['sleep', 'go to sleep']:
        result = pel_sleep_face()
    elif msg in ['wake', 'wake up']:
        result = pel_wake_face()
    elif msg.startswith('ping'):
        parts = msg.split()
        result = pel_ping(parts[1] if len(parts) > 1 else 'google.com')
    elif msg.startswith("remember:"): result = remember(raw[9:].strip())
    elif msg == "recall": result = recall()
    elif msg.startswith("recall "): result = recall(msg[7:].strip())
    elif msg == "forget all": result = forget_all()
    elif msg in ["save","push","git push"]: result = git_push("Pel auto save")
    elif msg.startswith("speak "):
        pel_speak(raw[6:])
        result = f'speaking: {raw[6:]}'

    if result:
        history.append({"role": "user", "content": raw})
        history.append({"role": "assistant", "content": str(result)})
        save_memory(history)
        set_state('speaking', str(result)[:40])
        await update.message.reply_text(str(result)[:4000])
    else:
        history.append({"role": "user", "content": raw})
        reply = await ask_llm([{"role": "system", "content": SYSTEM}] + history[-20:])
        history.append({"role": "assistant", "content": reply})
        save_memory(history)
        text, spoken = parse_voice(reply)
        set_state('speaking', text[:40])
        if spoken:
            pel_speak(spoken)
        await update.message.reply_text(text)

    await asyncio.sleep(2)
    set_state('idle')

async def post_init(application):
    application.job_queue.run_repeating(heartbeat, interval=120, first=10)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", cmd_help))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
print("Pel running...")
from pel_startup_check import run_checks
run_checks()
start_scheduler()
start_proactive(app.bot, get_chat_id())
set_state('idle')
try:
    app.run_polling(drop_pending_updates=True)
except Exception as e:
    import asyncio
    from pel_self_repair import save_error, run_repair
    save_error(str(e))
    print(f"Crash: {e} - attempting self repair")
    asyncio.run(run_repair())

