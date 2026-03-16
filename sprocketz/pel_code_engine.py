import os, re, subprocess
from datetime import datetime

CODE_DIR = os.path.expanduser('~/sprocketz/code/')

def run_code_file(filepath, language='python'):
    runners = {'python':['python3',filepath],'bash':['bash',filepath],'sh':['bash',filepath],'javascript':['node',filepath],'js':['node',filepath]}
    cmd = runners.get(language.lower())
    if not cmd: return True, f'written to {filepath}'
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=CODE_DIR)
        return r.returncode==0, (r.stdout+r.stderr).strip() or 'no output'
    except subprocess.TimeoutExpired: return False, 'timed out'
    except Exception as e: return False, str(e)

def extract_code_block(text):
    m = re.search(r'```(\w+)?\n(.*?)```', text, re.DOTALL)
    if m: return (m.group(1) or 'python').lower(), m.group(2).strip()
    return 'python', text.strip() if text.strip() else 'print("Pel code engine online")'

def get_ext(lang):
    return {'python':'.py','bash':'.sh','sh':'.sh','javascript':'.js','js':'.js','html':'.html'}.get(lang,'.py')

async def pel_code(description, bot, chat_id, ask_llm, SYSTEM, CODER):
    await bot.send_message(chat_id=chat_id, text=f"🧠 On it: {description}")
    messages = [{"role":"system","content":CODER},{"role":"user","content":f"Write code to: {description}"}]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    success, filepath, output = False, None, ''
    for i in range(1, 6):
        await bot.send_message(chat_id=chat_id, text=f"⚙️ Pass {i}/5...")
        response = await ask_llm(messages, model="deepseek/deepseek-r1:free")
        language, code = extract_code_block(response)
        print(f"DEBUG lang={language} code_len={len(code)} preview={repr(code[:100])}")
        filepath = os.path.join(CODE_DIR, f"pel_{timestamp}{get_ext(language)}")
        with open(filepath, 'w') as f: f.write(code)
        success, output = run_code_file(filepath, language)
        if success:
            await bot.send_message(chat_id=chat_id, text=f"✅ Pass {i}.\n\n{output[:800]}")
            break
        else:
            await bot.send_message(chat_id=chat_id, text=f"❌ {output[:400]}\n🔁 Fixing...")
            messages.append({"role":"assistant","content":response})
            messages.append({"role":"user","content":f"Failed:\n{output}\n\nFix it. Code block only."})
    if not success:
        await bot.send_message(chat_id=chat_id, text=f"💀 Failed after 5.\n{output[:400]}")
        return
    summary = await ask_llm([{"role":"system","content":SYSTEM},{"role":"user","content":f"One dry Banksy sentence: {description}"}])
    await bot.send_message(chat_id=chat_id, text=f"🎨 {summary}\n\n📁 code/{os.path.basename(filepath)}")
