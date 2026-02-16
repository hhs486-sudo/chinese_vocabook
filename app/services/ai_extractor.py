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
