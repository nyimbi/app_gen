# File: gen_app/generators/code.py
import asyncio
import json
import logging
import os
from sqlalchemy import create_engine, MetaData, inspect

from gen_app.utils.formatting import (
    extract_code_block,
    format_code,
    validate_python_code,
)


async def generate_sqlalchemy_models(
    database_url: str, output_dir: str, model: str, llm_provider
) -> None:
    """
    Generate SQLAlchemy models by introspecting a PostgreSQL database.

    Parameters
    ----------
    database_url : str
        SQLAlchemy connection URL (e.g., postgresql://user:pass@host/dbname)
    output_dir : str
        Directory where generated models will be saved.
    model : str
        LLM model to use for generation.
    llm_provider : LLMProvider
        LLM provider instance.
    """
    try:
        engine = create_engine(database_url)
        inspector = inspect(engine)
        schema = "public"
        metadata = MetaData(schema=schema)
        metadata.reflect(engine, views=False)
        tables_info = []
        for table in inspector.get_table_names(schema=schema):
            columns = inspector.get_columns(table, schema=schema)
            pk = inspector.get_pk_constraint(table, schema=schema)
            fks = inspector.get_foreign_keys(table, schema=schema)
            indices = inspector.get_indexes(table, schema=schema)
            tables_info.append(
                {
                    "name": table,
                    "columns": columns,
                    "primary_key": pk.get("constrained_columns", []),
                    "foreign_keys": fks,
                    "indices": indices,
                }
            )
        prompt = f"""Generate SQLAlchemy ORM models for the following tables:
{json.dumps(tables_info, indent=2)}
Include proper type annotations (SQLAlchemy 2.0 style), relationships, __repr__ methods, and docstrings.
"""
        response = await llm_provider.generate_with_retry(prompt, model)
        code = extract_code_block(response.get("response", ""), language="python")
        if validate_python_code(code):
            formatted_code = await format_code(code)
            os.makedirs(output_dir, exist_ok=True)
            with open(os.path.join(output_dir, "models.py"), "w") as f:
                f.write(formatted_code)
            logging.info("SQLAlchemy models generated successfully.")
        else:
            logging.error("Generated SQLAlchemy models contain syntax errors.")
    except Exception as e:
        logging.error(f"Error generating SQLAlchemy models: {e}")
        raise
