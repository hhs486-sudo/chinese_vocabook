import logging
import os
import traceback
import uuid

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from app.models.schemas import ExtractResponse, GenerateRequest, WordEntry
from app.services.ai_extractor import extract_words
from app.services.word_generator import generate_word

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/api")

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "temp")


@router.post("/upload")
async def upload_images(files: list[UploadFile] = File(...)):
    """Upload one or more images and extract Chinese words."""
    try:
        if not files:
            raise HTTPException(status_code=400, detail="파일을 선택해주세요.")

        job_id = str(uuid.uuid4())
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        all_words = []
        seen = set()

        for file in files:
            logger.info(f"Processing file: {file.filename}, type: {file.content_type}")

            if not file.content_type or not file.content_type.startswith("image/"):
                raise HTTPException(
                    status_code=400,
                    detail=f"이미지 파일만 업로드 가능합니다: {file.filename}",
                )

            ext = os.path.splitext(file.filename or "img.jpg")[1]
            temp_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}{ext}")
            content = await file.read()
            with open(temp_path, "wb") as f:
                f.write(content)

            logger.info(f"Saved temp file: {temp_path} ({len(content)} bytes)")

            try:
                words = await extract_words(temp_path)
                logger.info(f"Extracted {len(words)} words")
                for w in words:
                    key = (w["chinese"], w["pinyin"])
                    if key not in seen:
                        seen.add(key)
                        all_words.append(w)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        return {
            "job_id": job_id,
            "words": [{"chinese": w["chinese"], "pinyin": w["pinyin"], "korean": w["korean"]} for w in all_words],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"서버 오류: {type(e).__name__}: {str(e)}"},
        )


@router.post("/generate")
async def generate_docx(request: GenerateRequest):
    """Generate a Word file from the (optionally edited) word list."""
    try:
        words = [w.model_dump() for w in request.words]
        if not words:
            raise HTTPException(status_code=400, detail="단어 목록이 비어있습니다.")

        output_path = generate_word(words, request.job_id)
        file_id = os.path.splitext(os.path.basename(output_path))[0]

        return {"download_id": file_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate error: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"서버 오류: {type(e).__name__}: {str(e)}"},
        )


@router.get("/download/{download_id}")
async def download_file(download_id: str):
    """Download the generated Word file."""
    file_path = os.path.join(UPLOAD_DIR, f"{download_id}.docx")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

    return FileResponse(
        path=file_path,
        filename="중국어단어장.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
