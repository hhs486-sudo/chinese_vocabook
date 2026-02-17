import base64
import json
import os
import re

from dotenv import load_dotenv

load_dotenv()

EXTRACT_PROMPT = """이미지에서 중국어 단어를 모두 추출하여 다음 JSON 형식으로만 응답하세요:
{"words": [{"chinese": "한자", "pinyin": "병음(성조 포함)", "korean": "한국어 뜻"}, ...]}

규칙:
1. 각 줄은 "한자 [병음] 한글뜻" 형식입니다
2. 한자 앞의 * 기호는 제거하세요
3. 병음은 [] 안의 텍스트만 추출하세요 (괄호 제외)
4. 한국어 뜻은 병음 뒤의 한글 텍스트 전체입니다
5. 이미지에 중국어가 없으면 {"words": []}
6. JSON 외 다른 텍스트는 절대 포함하지 마세요"""


def _encode_image(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _get_media_type(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    return types.get(ext, "image/jpeg")


async def extract_words_anthropic(file_path: str) -> list[dict]:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    image_data = _encode_image(file_path)
    media_type = _get_media_type(file_path)

    message = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": EXTRACT_PROMPT},
                ],
            }
        ],
    )
    return _parse_response(message.content[0].text)


async def extract_words_openai(file_path: str) -> list[dict]:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    image_data = _encode_image(file_path)
    media_type = _get_media_type(file_path)

    response = await client.chat.completions.create(
        model="gpt-4o",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_data}"
                        },
                    },
                    {"type": "text", "text": EXTRACT_PROMPT},
                ],
            }
        ],
    )
    return _parse_response(response.choices[0].message.content)


def _parse_response(text: str) -> list[dict]:
    text = text.strip()
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        data = json.loads(json_match.group())
        return data.get("words", [])
    return []


async def extract_words(file_path: str) -> list[dict]:
    provider = os.getenv("AI_PROVIDER", "anthropic").lower()
    if provider == "openai":
        return await extract_words_openai(file_path)
    return await extract_words_anthropic(file_path)


# ===== Workbook Extraction =====

WORKBOOK_DETECT_PROMPT = """이미지는 중국어 교재 페이지입니다. 이미지의 유형을 판별하세요.

유형 1 (type1): 표(테이블) 형식으로 한자, 병음, 의미, 예문이 행으로 나열된 페이지 (다음자, 전치사, 어휘 정리표 등)
유형 2 (type2): 대화문이 있는 유형학습 페이지 (A:, B: 등 화자별 대화 본문 + 본문해석이 분리되어 있는 구조)

반드시 다음 JSON 형식으로만 응답하세요:
{"type": "type1"} 또는 {"type": "type2"}

JSON 외 다른 텍스트는 절대 포함하지 마세요."""

WORKBOOK_TYPE1_PROMPT = """이미지는 중국어 교재의 표 형식 페이지입니다 (다음자, 전치사 등).
각 행에서 한자, 병음, 의미, 예문을 추출하여 다음 JSON 형식으로만 응답하세요:
{"entries": [{"chinese": "한자", "pinyin": "병음(성조 포함)", "meaning": "한국어 의미", "example": "중국어 예문 원문"}, ...]}

규칙:
1. 표의 각 행이 하나의 entry입니다. 같은 한자라도 병음이나 의미가 다르면 별도의 entry로 분리하세요.
2. 한자 앞의 * 기호는 제거하세요
3. 예문(example)은 표에서 중국어로 된 예문 문장을 반드시 추출하세요. 예문이 이미지에 있는데 누락하지 마세요.
4. 예문이 이미지에 정말 없는 행만 example을 빈 문자열로 처리합니다.
5. 의미(meaning)가 여러 개일 경우 쉼표로 구분합니다
6. 예문(example)은 중국어 원문만 추출하세요 (한국어 해석 제외, 병음 제외)
7. 이미지를 꼼꼼히 확인하여 모든 행의 예문을 빠짐없이 추출하세요.
8. JSON 외 다른 텍스트는 절대 포함하지 마세요"""

WORKBOOK_TYPE2_PROMPT = """이미지는 중국어 교재의 유형학습 페이지입니다.
A, B 등 화자별 대화가 있고, 별도로 본문해석(한국어 번역)이 있습니다.
각 화자의 발화에서 중국어 본문(한자)과 한국어 해석을 추출하여 다음 JSON 형식으로만 응답하세요:
{"entries": [{"speaker": "A", "chinese_text": "중국어 본문(한자만, 병음 제외)", "korean": "한국어 해석"}, ...]}

규칙:
1. speaker는 원문에 표시된 화자 레이블(A, B 등)을 그대로 사용합니다
2. chinese_text는 한자로 된 중국어 본문만 추출합니다 (병음은 제외)
3. korean은 본문해석 섹션에서 해당 화자의 한국어 번역을 추출합니다
4. 한 화자의 연속된 발화는 하나의 entry로 합칩니다
5. 본문과 해석이 페이지 내에서 분리되어 있더라도 speaker와 발화 순서를 기준으로 매칭합니다
6. 어휘 섹션은 제외합니다
7. JSON 외 다른 텍스트는 절대 포함하지 마세요"""


def _parse_workbook_response(text: str) -> list[dict]:
    text = text.strip()
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        data = json.loads(json_match.group())
        return data.get("entries", [])
    return []


async def _extract_workbook_anthropic(file_path: str, prompt: str) -> list[dict]:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    image_data = _encode_image(file_path)
    media_type = _get_media_type(file_path)

    message = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    return _parse_workbook_response(message.content[0].text)


async def _extract_workbook_openai(file_path: str, prompt: str) -> list[dict]:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    image_data = _encode_image(file_path)
    media_type = _get_media_type(file_path)

    response = await client.chat.completions.create(
        model="gpt-4o",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_data}"
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    return _parse_workbook_response(response.choices[0].message.content)


async def _detect_type_anthropic(file_path: str) -> str:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    image_data = _encode_image(file_path)
    media_type = _get_media_type(file_path)

    message = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": WORKBOOK_DETECT_PROMPT},
                ],
            }
        ],
    )
    return _parse_type_response(message.content[0].text)


async def _detect_type_openai(file_path: str) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    image_data = _encode_image(file_path)
    media_type = _get_media_type(file_path)

    response = await client.chat.completions.create(
        model="gpt-4o",
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_data}"
                        },
                    },
                    {"type": "text", "text": WORKBOOK_DETECT_PROMPT},
                ],
            }
        ],
    )
    return _parse_type_response(response.choices[0].message.content)


def _parse_type_response(text: str) -> str:
    text = text.strip()
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        data = json.loads(json_match.group())
        detected = data.get("type", "type1")
        if detected in ("type1", "type2"):
            return detected
    return "type1"


async def detect_workbook_type(file_path: str) -> str:
    """Auto-detect workbook type from image using AI."""
    provider = os.getenv("AI_PROVIDER", "anthropic").lower()
    if provider == "openai":
        return await _detect_type_openai(file_path)
    return await _detect_type_anthropic(file_path)


async def extract_workbook(file_path: str, workbook_type: str) -> list[dict]:
    prompt = WORKBOOK_TYPE1_PROMPT if workbook_type == "type1" else WORKBOOK_TYPE2_PROMPT
    provider = os.getenv("AI_PROVIDER", "anthropic").lower()
    if provider == "openai":
        return await _extract_workbook_openai(file_path, prompt)
    return await _extract_workbook_anthropic(file_path, prompt)


# ===== Combined Detect + Extract (single API call) =====

WORKBOOK_COMBINED_PROMPT = """이미지는 중국어 교재 페이지입니다. 유형을 판별하고 내용을 추출하세요.

유형 1 (type1): 표(테이블) 형식으로 한자, 병음, 의미, 예문이 행으로 나열된 페이지
유형 2 (type2): 대화문이 있는 유형학습 페이지 (A:, B: 등 화자별 대화)

유형 1인 경우 다음 JSON으로 응답:
{"type": "type1", "entries": [{"chinese": "한자", "pinyin": "병음(성조 포함)", "meaning": "한국어 의미", "example": "중국어 예문 원문"}, ...]}

유형 1 규칙:
- 표의 각 행이 하나의 entry. 같은 한자라도 병음/의미가 다르면 별도 entry
- 한자 앞의 * 기호 제거
- 예문(example)은 중국어 원문만 (한국어 해석/병음 제외)
- 예문이 정말 없는 행만 빈 문자열 처리
- 의미가 여러 개면 쉼표 구분

유형 2인 경우 다음 JSON으로 응답:
{"type": "type2", "entries": [{"speaker": "A", "chinese_text": "중국어 본문(한자만)", "korean": "한국어 해석"}, ...]}

유형 2 규칙:
- speaker는 원문 화자 레이블(A, B 등) 그대로
- chinese_text는 한자 본문만 (병음 제외)
- korean은 본문해석에서 해당 화자의 한국어 번역
- 어휘 섹션 제외

JSON 외 다른 텍스트는 절대 포함하지 마세요."""


def _parse_combined_response(text: str) -> dict:
    text = text.strip()
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        data = json.loads(json_match.group())
        wb_type = data.get("type", "type1")
        if wb_type not in ("type1", "type2"):
            wb_type = "type1"
        return {"type": wb_type, "entries": data.get("entries", [])}
    return {"type": "type1", "entries": []}


async def _combined_extract_anthropic(file_path: str) -> dict:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    image_data = _encode_image(file_path)
    media_type = _get_media_type(file_path)

    message = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": WORKBOOK_COMBINED_PROMPT},
                ],
            }
        ],
    )
    return _parse_combined_response(message.content[0].text)


async def _combined_extract_openai(file_path: str) -> dict:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    image_data = _encode_image(file_path)
    media_type = _get_media_type(file_path)

    response = await client.chat.completions.create(
        model="gpt-4o",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_data}"
                        },
                    },
                    {"type": "text", "text": WORKBOOK_COMBINED_PROMPT},
                ],
            }
        ],
    )
    return _parse_combined_response(response.choices[0].message.content)


async def detect_and_extract_workbook(file_path: str) -> dict:
    """Detect type and extract workbook content in a single API call."""
    provider = os.getenv("AI_PROVIDER", "anthropic").lower()
    if provider == "openai":
        return await _combined_extract_openai(file_path)
    return await _combined_extract_anthropic(file_path)
