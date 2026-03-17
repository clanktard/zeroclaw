import os, subprocess

SPROCKETZ = os.path.expanduser('~/sprocketz')
ZEROCLAW = os.path.expanduser('~/zeroclaw')
FILES = ['agent.py','pel_code_engine.py','pel_memory_engine.py','pel_self_repair.py','pel_scheduler.py','pel_autowire.py','pel_proactive.py','pel_git.py']

def git_push(message='auto update'):
    try:
        for f in FILES:
            src = os.path.join(SPROCKETZ, f)
            dst = os.path.join(ZEROCLAW, 'sprocketz', f)
            if os.path.exists(src): subprocess.run(['cp', src, dst], check=True)
        subprocess.run(['git', '-C', ZEROCLAW, 'add', '.'], capture_output=True)
        r = subprocess.run(['git', '-C', ZEROCLAW, 'commit', '-m', message], capture_output=True, text=True)
        if 'nothing to commit' in r.stdout: return 'Nothing to push.'
        r = subprocess.run(['git', '-C', ZEROCLAW, 'push'], capture_output=True, text=True)
        return 'Pushed to GitHub.' if r.returncode == 0 else f'Push failed: {r.stderr[:200]}'
    except Exception as e:
        return f'Git error: {e}'
