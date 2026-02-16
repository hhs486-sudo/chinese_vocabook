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


# ===== Workbook Models =====

class WorkbookType1Entry(BaseModel):
    chinese: str
    pinyin: str
    meaning: str
    example: str = ""


class WorkbookType2Entry(BaseModel):
    speaker: str
    korean: str
    chinese_text: str


class WorkbookExtractResponse(BaseModel):
    job_id: str
    entries: list[dict]


class WorkbookGenerateRequest(BaseModel):
    job_id: str
    workbook_type: str
    entries: list[dict]
