import ast
import re
from typing import Tuple, List, Dict, Any
import logging

logger = logging.getLogger("appgen")


class CodeVerifier:
    @staticmethod
    def verify_syntax(code: str) -> Tuple[bool, str]:
        try:
            compile(code, "<string>", "exec")
            return True, ""
        except SyntaxError as e:
            line_num = e.lineno or "?"
            col_num = e.offset or "?"
            lines = code.split("\n")
            start_line = max(0, line_num - 3) if isinstance(line_num, int) else 0
            end_line = (
                min(len(lines), line_num + 2)
                if isinstance(line_num, int)
                else min(5, len(lines))
            )
            context_lines = [
                f"{'>>> ' if i == line_num - 1 else '    '}{i+1}: {lines[i]}"
                for i in range(start_line, end_line)
                if i < len(lines)
            ]
            return (
                False,
                f"Syntax error ({type(e).__name__}) at line {line_num}, column {col_num}: {str(e)}\nContext:\n{'\n'.join(context_lines)}",
            )
        except Exception as e:
            return False, f"Compilation error: {str(e)}"

    @staticmethod
    def verify_imports(code: str) -> Tuple[bool, List[str], str]:
        try:
            tree = ast.parse(code)
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(name.name for name in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)
            return True, imports, ""
        except Exception as e:
            return False, [], f"Import verification error: {str(e)}"

    @staticmethod
    def verify_component_structure(
        code: str, component_type: str, component_name: str
    ) -> Tuple[bool, Dict[str, Any], str]:
        try:
            tree = ast.parse(code)
            if component_type.lower() == "class":
                class_nodes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
                if not class_nodes:
                    return False, {}, "No class definitions found"
                target = next(
                    (c for c in class_nodes if c.name == component_name), None
                )
                if not target:
                    return (
                        False,
                        {"found_classes": [c.name for c in class_nodes]},
                        f"Expected class '{component_name}' not found",
                    )
                methods = [
                    {
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "is_static": any(
                            isinstance(dec, ast.Name) and dec.id == "staticmethod"
                            for dec in node.decorator_list
                        ),
                        "is_class": any(
                            isinstance(dec, ast.Name) and dec.id == "classmethod"
                            for dec in node.decorator_list
                        ),
                    }
                    for node in target.body
                    if isinstance(node, ast.FunctionDef)
                ]
                return (
                    True,
                    {
                        "type": "class",
                        "name": target.name,
                        "methods": methods,
                        "has_init": any(m["name"] == "__init__" for m in methods),
                        "base_classes": [
                            ast.unparse(base).strip() for base in target.bases
                        ],
                    },
                    "",
                )
            # Similar implementations for function and module types...
        except Exception as e:
            return False, {}, f"Structure verification error: {str(e)}"

    @staticmethod
    def repair_syntax_errors(code: str, error_info: str) -> str:
        # Implementation remains similar but simplified for brevity
        return code  # Placeholder

    @staticmethod
    def verify_component_dependencies(
        code: str, component_dependencies: List[str]
    ) -> Tuple[bool, List[str], str]:
        try:
            tree = ast.parse(code)
            referenced_names = {
                node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
            }
            missing = [
                dep
                for dep in component_dependencies
                if dep.split(".")[0] not in referenced_names
            ]
            return (
                not missing,
                missing,
                f"Component does not reference dependencies: {', '.join(missing)}"
                if missing
                else "",
            )
        except Exception as e:
            return False, [], f"Dependency verification error: {str(e)}"
