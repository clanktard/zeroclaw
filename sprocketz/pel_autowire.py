
import ast
import os
import sys

def validate_python_syntax(code):
    """Validates Python syntax of a given code string using ast.parse().

    Args:
        code: A string containing Python code.

    Returns:
        True if the syntax is valid, False otherwise.
    """
    try:
        ast.parse(code)
        return True
    except SyntaxError as e:
        print("Syntax error found in code:", file=sys.stderr)
        print(e, file=sys.stderr)
        return False

def generate_agent_code():
    # This function placeholder represents the original code generation logic
    # that was in `pel_autowire.py`.
    # In a real scenario, you would extract the actual code generation logic
    # from the original `pel_autowire.py` and place it here.

    # For demonstration, we'll create a sample code snippet.
    # You can change this to `invalid_agent_code` to test the error handling.
    valid_agent_code = '''
def greet(name):
    print("Hello, " + name)

class MyClass:
    def __init__(self, value):
        self.value = value

    def get_value(self):
        return self.value
'''

    # Uncomment the following line to test the syntax error handling
    # invalid_agent_code = '''
# def greet(name) # Missing colon
#     print("Hello, " + name)
# '''
    # return invalid_agent_code

    return valid_agent_code


if __name__ == "__main__":
    # Determine the sprocketz directory dynamically if possible,
    # or assume it's a known path.
    # For this example, we'll assume `pel_autowire.py` is within `sprocketz_dir`.
    sprocketz_dir = os.path.dirname(os.path.abspath(__file__))
    agent_path = os.path.join(sprocketz_dir, "agent.py")

    print("Generating code for agent.py...")
    generated_code = generate_agent_code()

    print("Validating Python syntax for generated agent.py code...")
    if validate_python_syntax(generated_code):
        print("Syntax validation passed. Saving to agent.py...")
        try:
            with open(agent_path, "w") as f:
                f.write(generated_code)
            print("Successfully wrote to agent.py.")
        except IOError as e:
            print("Error writing to {}: {}".format(agent_path, e), file=sys.stderr)
            sys.exit(1)
    else:
        print("Aborting save to agent.py due to syntax errors.", file=sys.stderr)
        sys.exit(1)
