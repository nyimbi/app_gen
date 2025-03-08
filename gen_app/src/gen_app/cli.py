# File: gen_app/cli.py
#!/usr/bin/env python3
"""
CLI for the Enhanced LLM-powered Python Project Generator.

Handles command-line argument parsing and interactive project setup.
"""

import argparse
import asyncio
import logging
import sys
import traceback

from gen_app.config import load_config
from gen_app.generators.project_generator import ProjectGenerator
from gen_app.utils.llm import OllamaProvider
from gen_app.utils.formatting import format_code


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Enhanced LLM-powered Python project generator"
    )
    parser.add_argument("--project", help="Project name")
    parser.add_argument(
        "--type", help="Project type (e.g., flask_api, sqlalchemy_models)"
    )
    parser.add_argument("--description", help="Project description")
    parser.add_argument("--model", help="LLM model to use")
    parser.add_argument(
        "--interactive", action="store_true", help="Run in interactive mode"
    )
    return parser.parse_args()


async def interactive_setup():
    print("=== Interactive Project Setup ===")
    project_name = input("Project name (default: my_project): ").strip() or "my_project"
    project_type = input("Project type (e.g., flask_api): ").strip() or "general_app"
    description = input("Project description: ").strip() or "A generated project."
    model = (
        input("LLM model (default: mistral-nemo:12b-instruct-2407-q8_0): ").strip()
        or "mistral-nemo:12b-instruct-2407-q8_0"
    )
    config = load_config()
    llm_provider = OllamaProvider()
    generator = ProjectGenerator(
        project_name=project_name,
        project_type=project_type,
        description=description,
        model=model,
        llm_provider=llm_provider,
        formatter=format_code,
        config=config,
    )
    return generator


async def main():
    args = parse_arguments()
    config = load_config()
    llm_provider = OllamaProvider()
    # Use interactive mode if specified or if required arguments are missing
    if args.interactive or not (args.project and args.description):
        generator = await interactive_setup()
    else:
        project_name = args.project
        project_type = args.type or "general_app"
        description = args.description
        model = args.model or config.get(
            "default_model", "mistral-nemo:12b-instruct-2407-q8_0"
        )
        generator = ProjectGenerator(
            project_name=project_name,
            project_type=project_type,
            description=description,
            model=model,
            llm_provider=llm_provider,
            formatter=format_code,
            config=config,
        )
    try:
        await generator.generate()
        print(f"\nProject generated successfully in '{generator.project_name}'")
    except Exception as e:
        logging.error(f"Error generating project: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
