import json
import re
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Request(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(min_length=1, max_length=12000)
    traceback: str = Field(min_length=1, max_length=6000)

    @field_validator("code", "traceback")
    @classmethod
    def meaningful(cls, value):
        if not value.strip():
            raise ValueError("Enter nonblank text")
        return value


class Diagnosis(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    category: str = Field(min_length=1, max_length=100)
    root_cause: str = Field(min_length=1, max_length=3000)
    corrected_code: str = Field(min_length=1, max_length=16000)
    explanation: str = Field(min_length=1, max_length=3000)


def parse(raw):
    match = re.fullmatch(r"\s*```(?:json)?\s*(.*?)\s*```\s*", raw, re.DOTALL)
    return Diagnosis.model_validate(json.loads(match.group(1) if match else raw))
