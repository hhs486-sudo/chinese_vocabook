from pydantic import BaseModel


class WordEntry(BaseModel):
    chinese: str
    pinyin: str
    korean: str


class ExtractResponse(BaseModel):
    job_id: str
    words: list[WordEntry]


class GenerateRequest(BaseModel):
    job_id: str
    words: list[WordEntry]
