# File: gen_app/generators/artifacts.py
"""
Module for generating project artifacts.

This module provides functions to generate deployment and configuration artifacts
(such as Docker Compose files, Kubernetes manifests, and CI/CD pipelines) using LLM.
"""

import asyncio
import logging
import os

from gen_app.utils.formatting import extract_code_block, format_code


async def generate_artifact(
    artifact_info: dict, project_name: str, model: str, llm_provider
) -> None:
    """
    Generate an artifact file using LLM.

    Parameters
    ----------
    artifact_info : dict
        Dictionary containing artifact file details (name, description, etc.).
    project_name : str
        Name of the project.
    model : str
        LLM model identifier.
    llm_provider : LLMProvider
        Instance of LLMProvider for generating artifact content.
    """
    prompt = f"""Generate a complete {artifact_info.get("name")} file for the project "{project_name}":
Description: {artifact_info.get("description")}
Ensure the file is production-ready, well-commented, and follows best practices.
"""
    try:
        response = await llm_provider.generate_with_retry(prompt, model)
        file_ext = artifact_info.get("name").split(".")[-1]
        content = extract_code_block(response.get("response", ""), language=file_ext)
        artifact_path = os.path.join(project_name, artifact_info.get("name"))
        os.makedirs(os.path.dirname(artifact_path), exist_ok=True)
        with open(artifact_path, "w") as f:
            f.write(content)
        logging.info(f"Artifact {artifact_info.get('name')} created successfully.")
    except Exception as e:
        logging.error(
            f"Artifact generation failed for {artifact_info.get('name')}: {e}"
        )


async def generate_all_artifacts(
    artifacts: list, project_name: str, model: str, llm_provider
) -> None:
    """
    Generate all specified artifact files concurrently.

    Parameters
    ----------
    artifacts : list
        List of artifact information dictionaries.
    project_name : str
        Name of the project.
    model : str
        LLM model identifier.
    llm_provider : LLMProvider
        Instance of LLMProvider.
    """
    tasks = []
    for artifact in artifacts:
        tasks.append(generate_artifact(artifact, project_name, model, llm_provider))
    await asyncio.gather(*tasks)
