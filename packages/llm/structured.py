import json
import logging
import re
from contextvars import ContextVar
from typing import TypeVar, Type
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Set by the parser in the same async task as the gateway call.  The
# orchestrator consumes it immediately when recording the corresponding
# AgentRun, so concurrent investigations cannot overwrite one another.
output_validation_status: ContextVar[str] = ContextVar(
    "output_validation_status", default="validated"
)

class StructuredOutputError(Exception):
    pass

class StructuredOutputParser:
    def parse(self, raw: str, schema: Type[T]) -> T:
        try:
            # Attempt to extract json if it is wrapped in markdown
            extracted_json = self._extract_json(raw)
            data = json.loads(extracted_json)
            parsed = schema(**data)
            output_validation_status.set("validated")
            return parsed
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"Initial parse failed: {e}. Attempting repair.")
            parsed = self._repair_and_parse(raw, schema)
            output_validation_status.set("repaired")
            return parsed
            
    def _extract_json(self, raw: str) -> str:
        # Match markdown json blocks
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
        if match:
            return match.group(1).strip()
        
        # If no markdown block, try to find the first '{' and last '}'
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            return raw[start:end+1]
            
        return raw.strip()

    def _repair_and_parse(self, raw: str, schema: Type[T]) -> T:
        try:
            # Basic repairs
            cleaned = raw.replace("'", '"')  # Sometimes single quotes are used
            # Replace trailing commas
            cleaned = re.sub(r",\s*([\]}])", r"\1", cleaned)
            
            extracted = self._extract_json(cleaned)
            data = json.loads(extracted)
            return schema(**data)
        except Exception as e:
            logger.error(f"Failed to repair JSON output. Raw output: {raw}")
            raise StructuredOutputError(f"Could not parse structured output: {e}")
