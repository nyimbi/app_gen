import re
import json
import logging
from core.exceptions import GenerationError

logger = logging.getLogger("appgen")


class OutputParser:
    @staticmethod
    def extract_code(raw_output: str) -> str:
        code_blocks = re.findall(r"```(?:python)?\s*([\s\S]*?)```", raw_output)
        if code_blocks:
            return "\n\n".join(block.strip() for block in code_blocks)
        lines = raw_output.strip().split("\n")
        code_indicators = [
            r"^import\s+",
            r"^from\s+.*\s+import\s+",
            r"^def\s+",
            r"^class\s+",
            r"^if\s+__name__\s+==",
            r"^\s+[a-zA-Z0-9_]+\s*=",
            r"^[a-zA-Z0-9_]+\s*=",
            r"^@[a-zA-Z0-9_]+",
        ]
        if any(any(re.match(pat, line) for pat in code_indicators) for line in lines):
            return raw_output.strip()
        return raw_output.strip()  # Simplified for brevity

    @staticmethod
    def extract_json(raw_output: str) -> str:
        json_blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)```", raw_output)
        if json_blocks:
            return max(json_blocks, key=len).strip()
        json_matches = re.findall(r"(\{[\s\S]*\})", raw_output)
        if json_matches:
            for match in sorted(json_matches, key=len, reverse=True):
                try:
                    json.loads(match.strip())
                    return match.strip()
                except json.JSONDecodeError:
                    continue
        return raw_output

    @staticmethod
    def clean_and_verify_json(json_str: str) -> dict:
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            clean_json = re.sub(r"'([^']*)':", r'"\1":', json_str)
            clean_json = re.sub(r",\s*\}", "}", clean_json)
            clean_json = re.sub(r",\s*\]", "]", clean_json)
            try:
                return json.loads(clean_json)
            except json.JSONDecodeError:
                raise GenerationError("Failed to parse JSON after cleaning attempts")
