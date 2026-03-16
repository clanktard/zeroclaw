import ast, os

AGENT_FILE = os.path.expanduser('~/sprocketz/agent.py')

def validate_syntax(code):
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, str(e)

def autowire(import_line, start_call=None):
    try:
        with open(AGENT_FILE) as f:
            source = f.read()
        if import_line in source:
            return f"Already wired: {import_line}"
        lines = source.split('\n')
        last_import = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                last_import = i
        lines.insert(last_import + 1, import_line)
        if start_call:
            for i, line in enumerate(lines):
                if 'Pel running...' in line:
                    lines.insert(i + 1, start_call)
                    break
        new_source = '\n'.join(lines)
        ok, err = validate_syntax(new_source)
        if not ok:
            return f"Syntax error - aborted: {err}"
        with open(AGENT_FILE, 'w') as f:
            f.write(new_source)
        return f"Wired: {import_line}"
    except Exception as e:
        return f"Autowire error: {e}"
