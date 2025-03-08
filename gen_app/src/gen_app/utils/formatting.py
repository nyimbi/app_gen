# File: gen_app/utils/formatting.py
"""
Formatting utilities for generated code.

Provides functions to extract code blocks from text, format code using external tools,
and validate Python syntax.
"""

import ast
import subprocess
import logging
import os
import re


def extract_code_block(response_text: str, language: str = "python") -> str:
    """
    Extract code block from text enclosed in triple backticks.

    Parameters
    ----------
    response_text : str
        The raw text response containing code.
    language : str, optional
        The programming language (default is "python").

    Returns
    -------
    str
        The extracted code block.
    """
    marker = f"```{language}"
    if marker in response_text:
        content = response_text.split(marker, 1)[1]
        return content.split("```", 1)[0].strip()
    elif "```" in response_text:
        return response_text.split("```", 1)[1].split("```", 1)[0].strip()
    return response_text.strip()


async def format_code(code_content: str) -> str:
    """
    Format Python code using isort and black.

    Parameters
    ----------
    code_content : str
        Raw Python code.

    Returns
    -------
    str
        Formatted Python code.
    """
    if not code_content.strip():
        return code_content
    temp_filename = "temp_format.py"
    with open(temp_filename, "w") as f:
        f.write(code_content)
    try:
        subprocess.run(["isort", temp_filename], check=True, capture_output=True)
        subprocess.run(["black", temp_filename], check=True, capture_output=True)
        with open(temp_filename, "r") as f:
            formatted_code = f.read()
        return formatted_code
    except Exception as e:
        logging.warning(f"Code formatting failed: {e}")
        return code_content
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


def validate_python_code(code: str) -> bool:
    """
    Validate Python code by parsing it.

    Parameters
    ----------
    code : str
        Python code to validate.

    Returns
    -------
    bool
        True if code is syntactically correct, else False.
    """
    try:
        ast.parse(code)
        return True
    except SyntaxError as e:
        logging.warning(f"Syntax error in generated code: {e}")
        return False
