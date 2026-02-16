# 중국어 학습 도우미 (Chinese Learning Helper)

## 프로젝트 개요
EBS 중국어 교재 사진에서 AI로 텍스트를 추출하여 MS Word 학습 자료를 자동 생성하는 웹 서비스.
- **배포**: https://chinese-vocabook.onrender.com/
- **GitHub**: https://github.com/hhs486-sudo/chinese_vocabook
- **로컬 실행**: `run.bat` → http://localhost:8000

## 기술 스택
- **백엔드**: Python 3.13 + FastAPI + Uvicorn
- **AI**: Anthropic Claude Sonnet 4.5 (기본) / OpenAI GPT-4o (대체) — `AI_PROVIDER` 환경변수로 전환
- **Word 생성**: python-docx
- **프론트엔드**: Vanilla JS + Jinja2 템플릿 (프레임워크 없음)
- **배포**: Render (Free Tier)

## 프로젝트 구조
```
app/
├── main.py                  # FastAPI 앱 진입점
├── api/routes.py            # API 엔드포인트 (단어장 3개 + 워크북 3개)
├── services/
│   ├── ai_extractor.py      # AI 이미지→텍스트 추출 (Vision API)
│   ├── word_generator.py    # 단어장 Word 생성 (템플릿 기반)
│   └── workbook_generator.py # 워크북 Word 생성 (Type1: 테이블, Type2: 문단)
├── models/schemas.py        # Pydantic 모델
└── utils/
templates/index.html         # 메인 페이지 (탭 UI)
static/
├── css/style.css
└── js/
    ├── main.js              # 탭 전환 + 단어장 로직 (IIFE)
    └── workbook.js          # 워크북 로직 (IIFE)
중국어단어장.docx              # 단어장 Word 템플릿 원본
temp/                        # 생성된 Word 파일 임시 저장
```

## 핵심 기능 2가지

### 1. 단어장 (탭 1)
- 사진 → AI가 `한자/병음/뜻` 추출 → Word 단어장 생성
- 템플릿(`중국어단어장.docx`) 기반, 29행×6열 테이블
- 셀 매핑: `cells[0]`=한자, `cells[3]`=병음, `cells[5]`=뜻
- 폰트: 한자 Microsoft YaHei 12pt, 병음/뜻 맑은 고딕
- 뜻 자동 폰트 축소 (최소 7pt), 다중 페이지 지원

### 2. 워크북 (탭 2)
- 사진 → AI가 유형 자동 감지 → 따라쓰기 워크북 생성
- **Type 1** (세로 테이블): 한자/병음/의미/예문 → 4열 테이블, 동적 컬럼 너비
- **Type 2** (유형학습): 대화문 → 본문해석(한국어) + 본문(중국어) 문단 형태
- 회색 한자(`#B0B0B0`, Microsoft YaHei 16pt) 위에 따라쓰기

## API 엔드포인트
| 경로 | 설명 |
|------|------|
| `POST /api/upload` | 단어장: 이미지→AI 단어 추출 |
| `POST /api/generate` | 단어장: Word 파일 생성 |
| `GET /api/download/{id}` | 단어장: 파일 다운로드 |
| `POST /api/workbook/upload` | 워크북: 이미지→유형감지+추출 |
| `POST /api/workbook/generate` | 워크북: Word 파일 생성 |
| `GET /api/workbook/download/{id}` | 워크북: 파일 다운로드 |

## 개발 규칙

### 코딩 컨벤션
- 한국어 주석/변수명 금지 (코드는 영어, UI/프롬프트만 한국어)
- 프론트엔드: IIFE 패턴으로 전역 스코프 격리, DOM ID 접두사 `vocab-`(단어장) / `wb-`(워크북)
- AI 응답 파싱: 정규식 `\{.*\}` (re.DOTALL)로 JSON 추출
- Word XML 직접 조작 시 python-docx + lxml 사용

### 환경변수 (.env)
- `AI_PROVIDER`: `anthropic` 또는 `openai`
- `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`
- .env 파일은 절대 커밋하지 않을 것

### 로컬 실행
```bash
# Windows
run.bat
# 또는 직접 실행
C:\Python313\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Git / 배포
- 원격 저장소: GitHub (hhs486-sudo/chinese_vocabook)
- 배포: GitHub push → Render 자동 배포
- `temp/`, `.env`, `__pycache__/`는 .gitignore에 포함

## 알려진 이슈 & 주의사항
- Windows Store python.exe 스텁 문제 → `C:\Python313\python.exe` 직접 사용
- 포트 8000 충돌 시 `run.bat`이 기존 프로세스 종료 후 3초 대기
- Render Free Tier: 15분 미사용 시 슬립, 콜드 스타트 지연 있음
- AI 프롬프트 수정 시 `ai_extractor.py` 상단 상수(`EXTRACT_PROMPT`, `WORKBOOK_*_PROMPT`) 참조

## 상세 문서
- 전체 기능 명세: [PROJECT.md](PROJECT.md)
