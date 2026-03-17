import os, re, subprocess, asyncio
from datetime import datetime

CODE_DIR = os.path.expanduser('~/sprocketz/code/')

def run_code_file(filepath, language='python'):
    runners = {'python':['python3',filepath],'bash':['bash',filepath],'sh':['bash',filepath],'javascript':['node',filepath],'js':['node',filepath]}
    cmd = runners.get(language.lower())
    if not cmd: return True, f'written to {filepath}'
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=CODE_DIR)
        return r.returncode==0, (r.stdout+r.stderr).strip() or 'no output'
    except subprocess.TimeoutExpired: return False, 'timed out'
    except Exception as e: return False, str(e)

def extract_code_block(text):
    m = re.search(r'```(\w+)?\n(.*?)```', text, re.DOTALL)
    if m: return (m.group(1) or 'python').lower(), m.group(2).strip()
    code = text.strip()
    if not code or len(code) > 2000 or '\n' not in code:
        code = 'print("Pel code engine online")'
    return 'python', code

def get_ext(lang):
    return {'python':'.py','bash':'.sh','sh':'.sh','javascript':'.js','js':'.js','html':'.html'}.get(lang,'.py')

async def pel_code(description, bot, chat_id, ask_llm, SYSTEM, CODER):
    await bot.send_message(chat_id=chat_id, text=f"🧠 On it: {description}")
    messages = [{"role":"user","content":f"{CODER}\n\nWrite code to: {description}"}]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    success, filepath, output = False, None, ''
    for i in range(1, 11):
        await bot.send_message(chat_id=chat_id, text=f"⚙️ Pass {i}/5...")
        await asyncio.sleep(3)
        response = await ask_llm(messages, model="openrouter/auto")
        language, code = extract_code_block(response)
        print(f"DEBUG lang={language} code_len={len(code)} preview={repr(code[:100])}")
        filepath = os.path.join(CODE_DIR, f"pel_{timestamp}{get_ext(language)}")
        if 'print(' not in code:
            code += '\nprint("done")'
        if 'print(' not in code:
            code += '\nprint("done")'
        if 'print(' not in code:
            code += '\nprint("done")'
        with open(filepath, 'w') as f: f.write(code)
        success, output = run_code_file(filepath, language)
        if success:
            await bot.send_message(chat_id=chat_id, text=f"✅ Pass {i}.\n\n{output[:800]}")
            await send_file_to_telegram(bot, chat_id, filepath)
            break
        else:
            await bot.send_message(chat_id=chat_id, text=f"❌ {output[:400]}\n🔁 Fixing...")
            messages.append({"role":"assistant","content":response})
            messages.append({"role":"user","content":f"Failed:\n{output}\n\nFix it. Code block only."})
    if not success:
        await bot.send_message(chat_id=chat_id, text=f"💀 Failed after 5.\n{output[:400]}")
        return
    summary = await ask_llm([{"role":"user","content":f"One dry Banksy sentence about what this code does: {description}"}], model="openrouter/auto")
    await bot.send_message(chat_id=chat_id, text=f"🎨 {summary}\n\n📁 code/{os.path.basename(filepath)}")

async def send_file_to_telegram(bot, chat_id, filepath):
    try:
        with open(filepath, "rb") as f:
            await bot.send_document(chat_id=chat_id, document=f)
    except Exception as e:
        print("send error: " + str(e))