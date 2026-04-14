import ast
from typing import Tuple, List

ALLOWED_IMPORTS = {
    'pandas', 'numpy', 'matplotlib', 'matplotlib.pyplot', 
    'datetime', 'json', 'math', 'os', 'io' 
}

def analyze_code_security(code_string: str) -> Tuple[bool, List[str]]:
    """
    Parses LLM-generated Python code into an AST and verifies that
    only strictly whitelisted modules are imported.
    """
    issues = []
    
    try:
        tree = ast.parse(code_string)
    except SyntaxError as e:
        return False, [f"Syntax Error at line {e.lineno}: {e.msg}"]
        
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                base_module = alias.name.split('.')[0]
                if base_module not in ALLOWED_IMPORTS:
                    issues.append(f"FORBIDDEN IMPORT: '{alias.name}'. Only data/charting libraries are allowed.")
                    
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                base_module = node.module.split('.')[0]
                if base_module not in ALLOWED_IMPORTS:
                    issues.append(f"FORBIDDEN IMPORT FROM: '{node.module}'.")
                    
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in ['eval', 'exec', 'open', '__import__', 'subprocess']:
                    issues.append(f"FORBIDDEN FUNCTION CALL: '{node.func.id}' is blocked by security policy.")
                    
    return len(issues) == 0, issues