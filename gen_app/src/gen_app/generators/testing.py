# File: gen_app/generators/testing.py
"""
Module for generating test files using LLM interactions.

This module provides functions to generate tests for individual functions
and for entire source files, ensuring comprehensive coverage.
"""

import asyncio
import json
import logging

from gen_app.utils.formatting import (
    extract_code_block,
    format_code,
    validate_python_code,
)


async def generate_tests_for_function(
    function_info: dict, file_info: dict, model: str, llm_provider
) -> str:
    """
    Generate pytest test cases for a specific function using the LLM.

    Parameters
    ----------
    function_info : dict
        Dictionary containing function details (name, description, parameters, etc.).
    file_info : dict
        Dictionary with file metadata (name, description).
    model : str
        LLM model identifier.
    llm_provider : LLMProvider
        LLM provider instance for generating test code.

    Returns
    -------
    str
        Generated test code for the function.
    """
    prompt = f"""Generate comprehensive pytest test cases for the function:
Function Name: {function_info.get("name")}
Description: {function_info.get("description")}
Parameters: {json.dumps(function_info.get("parameters", []))}
Return Type: {function_info.get("return_type", "None")}
File Purpose: {file_info.get("description")}
Ensure coverage of normal, edge, and error cases. Use fixtures where appropriate.
"""
    try:
        response = await llm_provider.generate_with_retry(prompt, model)
        test_code = extract_code_block(response.get("response", ""), language="python")
        return test_code
    except Exception as e:
        logging.warning(
            f"Test generation failed for function {function_info.get('name')}: {e}"
        )
        return f"# TODO: Add tests for {function_info.get('name')}\n"


async def generate_tests_for_file(
    file_info: dict,
    functions: list,
    project_name: str,
    model: str,
    llm_provider,
    blueprint_name: str = None,
) -> None:
    """
    Generate a complete test file for a given source file.

    Parameters
    ----------
    file_info : dict
        Dictionary containing file name and description.
    functions : list
        List of function dictionaries extracted from the file.
    project_name : str
        Name of the project.
    model : str
        LLM model identifier.
    llm_provider : LLMProvider
        LLM provider instance for generating test code.
    blueprint_name : str, optional
        Blueprint name if applicable.
    """
    import os

    test_file_name = f"test_{file_info.get('name').split('/')[-1]}"
    test_file_path = os.path.join(project_name, "tests", test_file_name)
    imports = f"import pytest\nfrom {file_info.get('name').replace('/', '.').replace('.py', '')} import *\n\n"
    test_codes = []
    for func in functions:
        test_code = await generate_tests_for_function(
            func, file_info, model, llm_provider
        )
        test_codes.append(test_code)
    all_tests = imports + "\n\n".join(test_codes)
    formatted_tests = await format_code(all_tests)
    os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
    with open(test_file_path, "w") as f:
        f.write(formatted_tests)
    logging.info(f"Test file {test_file_name} created successfully.")
