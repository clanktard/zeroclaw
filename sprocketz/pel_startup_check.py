import ast, os, subprocess

SPROCKETZ = os.path.expanduser('~/sprocketz')
ZEROCLAW = os.path.expanduser('~/zeroclaw')

def run_checks():
    fixed = []
    for f in os.listdir(SPROCKETZ):
        if not f.endswith('.py'): continue
        path = os.path.join(SPROCKETZ, f)
        try:
            with open(path) as fp: ast.parse(fp.read())
        except SyntaxError:
            subprocess.run(['git','-C',ZEROCLAW,'checkout','origin/master','--',f'sprocketz/{f}'], capture_output=True)
            subprocess.run(['cp', os.path.join(ZEROCLAW,'sprocketz',f), path])
            fixed.append(f)
    if fixed: print(f"Restored: {', '.join(fixed)}")
    else: print("All modules OK")
