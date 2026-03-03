import json
import re
import uuid
from typing import List, Optional, Tuple

from nala.athomic.ai.schemas.llms import LLMResponse
from nala.athomic.ai.schemas.tools import ToolCall
from nala.athomic.observability import get_logger

logger = get_logger(__name__)


class AgentResponseParser:
    """
    Advanced parser with JSON repair capabilities.

    Handles common LLM formatting errors such as:
    - Leaked JSON in text content.
    - Single quotes instead of double quotes.
    - Missing quotes around string values (e.g., "id": meu_id).
    """

    def parse(self, response: LLMResponse) -> Tuple[Optional[str], List[ToolCall]]:
        content = response.content
        tool_calls = response.tool_calls or []

        if tool_calls:
            return content, tool_calls

        if content and "{" in content:
            extracted_calls, remaining_content = self._extract_json_tool_calls(content)
            if extracted_calls:
                return remaining_content, extracted_calls

        return content, tool_calls

    def _sanitize_json_string(self, json_str: str) -> str:
        """
        Repairs common JSON structural errors before parsing.
        """
        # 1. Replace single quotes with double quotes
        json_str = json_str.replace("'", '"')

        # It looks for : followed by a non-quoted string that isn't true/false/null/number
        def quote_value(match):
            key_part = match.group(1)
            val_part = match.group(2).strip()

            # If value is already quoted or is a reserved JSON word/number, leave it
            if (
                val_part.startswith('"')
                or val_part.lower() in ["true", "false", "null"]
                or val_part.replace(".", "", 1).isdigit()
            ):
                return f"{key_part}: {val_part}"

            return f'{key_part}: "{val_part}"'

        # Regex to find key-value pairs
        json_str = re.sub(r'("[\w]+"\s*):([\s\w\-]+)', quote_value, json_str)

        return json_str

    def _extract_json_tool_calls(
        self, text: str
    ) -> Tuple[List[ToolCall], Optional[str]]:
        tool_calls: List[ToolCall] = []
        matches = re.finditer(r"(\{.*\})", text, re.DOTALL)

        last_match_end = 0
        cleaned_text_parts = []

        for match in matches:
            raw_json = match.group(1)
            try:
                # Apply the repair logic
                repaired_json = self._sanitize_json_string(raw_json)
                data = json.loads(repaired_json)

                # Extraction logic for name and args
                name = data.get("name") or data.get("function", {}).get("name")
                args = data.get("parameters") or data.get("arguments") or {}

                if name:
                    tool_calls.append(
                        ToolCall(
                            id=f"rec_{uuid.uuid4().hex[:8]}", name=name, arguments=args
                        )
                    )
                    cleaned_text_parts.append(text[last_match_end : match.start()])
                    last_match_end = match.end()
            except Exception as e:
                logger.debug(f"Failed to parse or repair JSON block: {e}")
                continue

        cleaned_text_parts.append(text[last_match_end:])
        final_content = "".join(cleaned_text_parts).strip()

        return tool_calls, final_content if final_content else None
