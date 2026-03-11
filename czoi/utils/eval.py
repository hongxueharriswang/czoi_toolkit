
import ast
import operator
# Safe evaluator for constraint conditions
# Based on https://stackoverflow.com/questions/30683844/safe-way-to-parse-user-supplied-mathematical-formula-in-python

def safe_eval(expr, context):
    """Safely evaluate a Python expression with restricted globals."""
    allowed_nodes = {
        ast.Expression, ast.BoolOp, ast.Compare, ast.BinOp, ast.UnaryOp,
        ast.Name, ast.Load, ast.Str, ast.Num, ast.List, ast.Tuple,
        ast.Dict, ast.Constant, ast.Attribute,
        # Operators
        ast.And, ast.Or, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow,
        ast.Not, ast.USub,
    }
    allowed_names = {
        # Builtins
        'abs', 'max', 'min', 'len', 'int', 'float', 'str',
        # Additional functions
        'datetime',
    }
    # Add context variables
    allowed_names.update(context.keys())

    def _check(node):
        if type(node) not in allowed_nodes:
            raise ValueError(f"Unsafe expression node: {type(node).__name__}")
        if isinstance(node, ast.Name):
            if node.id not in allowed_names:
                raise ValueError(f"Unsafe variable: {node.id}")
        # Recursively check children
        for child in ast.iter_child_nodes(node):
            _check(child)

    _check(ast.parse(expr, mode='eval').body)
    # Evaluate with context as globals and restricted builtins
    return eval(expr, {"__builtins__": {}}, context)
