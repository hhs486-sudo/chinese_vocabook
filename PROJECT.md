# 중국어 학습 도우미 (Chinese Learning Helper)

## 1. 프로젝트 개요

EBS 중국어 교재 사진에서 AI로 텍스트를 추출하여 MS Word 기반 학습 자료를 자동 생성하는 웹 서비스.
두 가지 기능(단어장 / 워크북)을 탭 UI로 제공한다.

- **URL (배포)**: https://chinese-vocabook.onrender.com/
- **GitHub**: https://github.com/hhs486-sudo/chinese_vocabook
- **로컬 실행**: `run.bat` 실행 후 http://localhost:8000 접속

---

## 2. 기능 개요

### 2.1 탭 구조

| 탭 | 기능명 | 설명 |
|----|--------|------|
| 단어장 | 중국어 단어장 | 사진에서 한자/병음/뜻을 추출하여 Word 단어장 생성 |
| 워크북 | 중국어 워크북 | 교재 사진에서 유형을 자동 감지하여 따라쓰기 워크북 생성 |

- 탭 전환은 `data-tab` 속성 기반, 각 탭은 독립적인 IIFE 스코프로 상태 관리

---

## 3. 단어장 (탭 1) — 기존 기능

### 3.1 기능 요구사항

| 구분 | 내용 |
|------|------|
| 이미지 업로드 | 여러 장의 사진을 동시에 업로드 (드래그 앤 드롭 지원) |
| AI 텍스트 추출 | 이미지에서 `한자 [병음] 한글뜻` 형식의 텍스트를 AI로 파싱 |
| 중복 제거 | 여러 이미지에 걸쳐 동일 단어(한자+병음 기준) 자동 중복 제거 |
| 결과 편집 | 추출된 단어 목록을 브라우저에서 인라인 편집/추가/삭제 가능 |
| Word 생성 | 기존 MS Word 템플릿(`중국어단어장.docx`)의 정해진 셀에 데이터 삽입 |
| 폰트 지정 | 한자: Microsoft YaHei 12pt, 병음: 맑은 고딕 12pt, 뜻: 맑은 고딕 11pt |
| 자동 폰트 축소 | 뜻 텍스트가 셀 너비를 초과할 경우 폰트 크기를 자동 축소하여 한 줄 유지 (최소 7pt) |
| 다중 페이지 | 단어 수가 템플릿 행을 초과하면 동일한 테이블 구조를 복제하여 다음 페이지 생성 |
| 파일 다운로드 | 생성된 `.docx` 파일을 `중국어단어장.docx`로 다운로드 |

### 3.2 입력 데이터 형식

사진 속 텍스트는 다음 형식을 따름:

```
*打扫 [dǎsǎo] 청소하다
检查 [jiǎnchá] 검사하다
```

- 각 줄: `한자 [병음] 한글뜻` (공백으로 구분)
- `*` 접두사: 제거 대상
- `[]` 내부: 병음 (성조 포함)
- 병음 뒤 한글: 한국어 뜻

### 3.3 AI 추출 프롬프트 (`EXTRACT_PROMPT`)

```
이미지에서 중국어 단어를 모두 추출하여 다음 JSON 형식으로만 응답하세요:
{"words": [{"chinese": "한자", "pinyin": "병음(성조 포함)", "korean": "한국어 뜻"}, ...]}
```

### 3.4 API 명세

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/upload` | 이미지 업로드 → AI 단어 추출 |
| POST | `/api/generate` | 편집된 단어 목록 → Word 파일 생성 |
| GET | `/api/download/{download_id}` | 생성된 Word 파일 다운로드 |

**POST `/api/upload`**
- Request: `multipart/form-data` — `files` (다중 이미지)
- Response:
  ```json
  {
    "job_id": "uuid",
    "words": [{"chinese": "打扫", "pinyin": "dǎsǎo", "korean": "청소하다"}, ...]
  }
  ```

**POST `/api/generate`**
- Request:
  ```json
  {
    "job_id": "uuid",
    "words": [{"chinese": "打扫", "pinyin": "dǎsǎo", "korean": "청소하다"}]
  }
  ```
- Response: `{"download_id": "file-uuid"}`

**GET `/api/download/{download_id}`**
- Response: `중국어단어장.docx` 파일

### 3.5 Word 생성 상세 (`word_generator.py`)

- 템플릿 파일(`중국어단어장.docx`)을 열고 Row 0부터 데이터 삽입 (헤더 행 없음)
- **테이블 구조**: 1개 테이블, 29행 (모두 데이터), 6열
- **셀 매핑**: `cells[0]` = 한자, `cells[3]` = 병음, `cells[5]` = 뜻
- **폰트 설정**: 한자 `Microsoft YaHei 12pt` (eastAsia 폰트 명시), 병음 `맑은 고딕 12pt`, 뜻 `맑은 고딕 11pt`
- **자동 폰트 축소**: 뜻 텍스트의 너비를 계산하여 셀에 한 줄로 들어가도록 폰트 크기 자동 조절
  - Full-width 문자 (한글, 한자) = 1.0 width unit
  - Half-width 문자 (ASCII, 공백, 구두점) = 0.5 width unit
  - 사용 가능 너비 = 셀 너비 - 셀 패딩 (모두 템플릿 XML에서 동적 읽기)
- **다중 페이지**: 단어 수 초과 시 템플릿 테이블 XML을 통째로 복제하여 동일 구조 유지

---

## 4. 워크북 (탭 2) — 신규 기능

### 4.1 기능 요구사항

교재 사진을 업로드하면 AI가 유형을 자동 감지하여 따라쓰기 워크북(Word)을 생성한다.
인쇄 시 회색 한자 위에 사용자가 직접 따라쓸 수 있도록 설계.

### 4.2 입력 이미지 유형

AI가 이미지를 분석하여 아래 두 유형 중 하나로 자동 분류한다.
여러 장 업로드 시 각 이미지별로 독립 분류되며, 두 유형이 동시에 나올 수 있다.

| 유형 | 이미지 특징 | 예시 |
|------|------------|------|
| Type 1 (세로 테이블) | 표 형식. 한자 → 병음 → 의미 → 예문이 행으로 나열 | 다음자, 전치사, 어휘 정리표 |
| Type 2 (유형학습) | 대화문 + 본문해석 구조. A:, B: 등 화자별 발화 | 유형학습 페이지 |

### 4.3 유형 자동 감지 + 추출 (통합 API 호출)

이미지 1장당 **1회의 AI API 호출**로 유형 판별과 내용 추출을 동시에 처리한다 (`WORKBOOK_COMBINED_PROMPT`).
여러 이미지를 업로드하면 `asyncio.gather`로 **병렬 처리**하여 속도를 극대화한다.

- 통합 프롬프트가 유형 판별 + 데이터 추출을 한 번에 수행
- 응답: `{"type": "type1", "entries": [...]}` 또는 `{"type": "type2", "entries": [...]}`
- 판별 실패 시 기본값 `type1`

> **이전 방식** (레거시, 코드 유지): 유형 감지 1회 + 추출 1회 = 이미지당 2회 호출, 순차 처리

### 4.4 Type 1 — 세로 테이블 워크북

#### 4.4.1 AI 추출 (`WORKBOOK_TYPE1_PROMPT`)

```json
{"entries": [{"chinese": "한자", "pinyin": "병음", "meaning": "한국어 의미", "example": "중국어 예문 원문"}, ...]}
```

추출 규칙:
1. 표의 각 행 = 하나의 entry. 같은 한자라도 병음/의미가 다르면 별도 entry
2. 한자 앞 `*` 기호 제거
3. 예문(example)은 중국어 원문만 추출 (한국어 해석, 병음 제외)
4. 예문이 이미지에 있으면 반드시 추출 (누락 금지)
5. 예문이 진짜 없는 행만 빈 문자열 처리
6. 의미가 여러 개이면 쉼표로 구분

#### 4.4.2 Word 생성 (`generate_workbook_type1`)

**페이지 설정:**
- A4, 상하 마진 1.5cm, 좌우 마진 2.0cm
- 사용 가능 너비: 17cm (≈481pt)

**테이블 구조:** 4열 (한자, 병음, 의미, 예문), 헤더 없음, `Table Grid` 스타일

**컬럼 너비 동적 계산 (핵심 로직):**
1. 모든 entry를 순회하여 한자 컬럼/예문 컬럼의 최대 텍스트 너비(pt) 계산
   - CJK 문자: `font_size_pt` 너비
   - ASCII 문자: `font_size_pt * 0.5` 너비
2. 셀 패딩 20pt 추가
3. 한자/예문 컬럼에 `noWrap` 설정 → 반드시 한 줄
4. 나머지 너비를 병음/의미 컬럼에 균등 분배 (2줄 허용)
5. 병음/의미 최소 너비 50pt 보장, 부족 시 한자/예문 컬럼 비례 축소

**폰트 규격:**

| 컬럼 | 폰트 | 크기 | 색상 | 줄바꿈 |
|------|------|------|------|--------|
| 한자 | Microsoft YaHei | 16pt | Gray (`#B0B0B0`) | 금지 (noWrap) |
| 병음 | 맑은 고딕 | 11pt | 기본 (검정) | 허용 |
| 의미 | 맑은 고딕 | 11pt | 기본 (검정) | 허용 |
| 예문 | Microsoft YaHei | 16pt | Gray (`#B0B0B0`) | 금지 (noWrap) |

**XML 조작:**
- `_set_cell_width()`: EMU → twips 변환 (1 twip = 635 EMU), `w:tcW` 설정
- `_set_cell_no_wrap()`: `w:noWrap` 요소 추가
- `_set_run_font()`: `w:rFonts`에 ascii, hAnsi, eastAsia 폰트 설정

### 4.5 Type 2 — 유형학습 워크북

#### 4.5.1 AI 추출 (`WORKBOOK_TYPE2_PROMPT`)

```json
{"entries": [{"speaker": "A", "chinese_text": "중국어 본문(한자만)", "korean": "한국어 해석"}, ...]}
```

추출 규칙:
1. speaker는 원문의 화자 레이블(A, B 등) 그대로 사용
2. chinese_text는 한자로 된 중국어 본문만 (병음 제외)
3. korean은 본문해석 섹션의 한국어 번역
4. 한 화자의 연속 발화는 하나의 entry로 합침
5. 본문과 해석이 분리되어 있어도 speaker + 순서 기준으로 매칭
6. 어휘 섹션은 제외

#### 4.5.2 Word 생성 (`generate_workbook_type2`)

**페이지 설정:** A4, 상하 마진 1.5cm, 좌우 마진 2.0cm

**출력 구조 (테이블이 아닌 문단 형태):**

각 entry마다 2줄을 연속 출력:
1. **한국어 해석** (본문해석) — `{speaker}: {korean}`
2. **중국어 본문** (따라쓰기용) — `{speaker}: {chinese_text}`

**핵심: 대화 간 빈 줄 없음**
- 모든 문단의 `space_before = Pt(0)`, `space_after = Pt(0)`
- 한국어 줄과 중국어 줄 사이에 별도 spacing 문단 없음
- 다음 entry의 한국어 줄도 바로 이어서 출력

**폰트 규격:**

| 줄 | 폰트 | 크기 | 색상 |
|----|------|------|------|
| 본문해석 (한국어) | 맑은 고딕 | 11pt | 기본 (검정) |
| 본문 (중국어) | Microsoft YaHei | 16pt | Gray (`#B0B0B0`) |

### 4.6 API 명세

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/workbook/upload` | 이미지 업로드 → 유형 자동 감지 + 내용 추출 |
| POST | `/api/workbook/generate` | 편집된 데이터 → Word 워크북 생성 |
| GET | `/api/workbook/download/{download_id}` | 생성된 Word 파일 다운로드 |

**POST `/api/workbook/upload`**

이미지별로 유형을 감지하고 추출하여 유형별로 분리 반환.

- Request: `multipart/form-data` — `files` (다중 이미지)
- Response:
  ```json
  {
    "job_id": "uuid",
    "type1_entries": [
      {"chinese": "向", "pinyin": "xiàng", "meaning": "~을 향하여", "example": "我向他借了一本书。"}
    ],
    "type2_entries": [
      {"speaker": "A", "chinese_text": "你好，请问你是哪国人？", "korean": "안녕하세요, 어느 나라 사람이세요?"}
    ]
  }
  ```
- 처리 흐름: 이미지마다 `detect_and_extract_workbook()` (통합 1회 호출) → 유형별 리스트에 추가
- 여러 이미지 업로드 시 `asyncio.gather`로 병렬 처리

**POST `/api/workbook/generate`**
- Request:
  ```json
  {
    "job_id": "uuid",
    "workbook_type": "type1",
    "entries": [{"chinese": "向", "pinyin": "xiàng", "meaning": "~을 향하여", "example": "..."}]
  }
  ```
- `workbook_type`: `"type1"` 또는 `"type2"`
- Response: `{"download_id": "file-uuid"}`

**GET `/api/workbook/download/{download_id}`**
- Response: `중국어워크북.docx` 파일

### 4.7 프론트엔드 (`workbook.js`)

- IIFE로 전역 스코프 격리
- 업로드 후 AI 응답에서 `type1_entries`와 `type2_entries`를 각각 확인
- 두 유형이 동시에 있으면 두 결과 섹션 모두 표시
- 각 유형별 편집 테이블 (행 추가/삭제/인라인 편집)
- Type 1 결과 테이블: #, 한자, 병음, 의미, 예문, 삭제
- Type 2 결과 테이블: #, 화자(width:40px), 본문해석(한국어), 본문(중국어), 삭제
- 워크북 생성 시 해당 유형의 entries만 서버로 전송
- **다운로드 후 돌아가기**: 두 유형이 동시에 추출된 경우, 한쪽을 다운로드한 뒤 "추출 결과로 돌아가기" 버튼으로 나머지 유형도 생성/다운로드 가능 (추출 데이터 보존)

---

## 5. 기술 스택

| 항목 | 기술 |
|------|------|
| 백엔드 | Python 3.13 + FastAPI |
| ASGI 서버 | Uvicorn |
| AI (기본) | Anthropic Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`) |
| AI (대체) | OpenAI GPT-4o |
| Word 처리 | python-docx |
| 프론트엔드 | HTML + CSS + JavaScript (Jinja2 템플릿, vanilla JS) |
| 배포 | Render (Free Tier) |
| 소스 관리 | GitHub |

### 5.1 의존성 (requirements.txt)

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6
python-docx>=1.1.0
anthropic>=0.20.0
openai>=1.10.0
Pillow>=10.0.0
aiofiles>=23.0.0
python-dotenv>=1.0.0
jinja2>=3.1.0
```

---

## 6. 프로젝트 구조

```
lilly_chinese_work/
├── app/
│   ├── main.py                     # FastAPI 앱 진입점, 글로벌 예외 핸들러
│   ├── api/
│   │   └── routes.py               # API 엔드포인트 (단어장 3개 + 워크북 3개)
│   ├── services/
│   │   ├── ai_extractor.py         # AI 이미지 추출 (단어장 + 워크북 유형감지/추출)
│   │   ├── word_generator.py       # 단어장 Word 생성 (템플릿 기반)
│   │   └── workbook_generator.py   # 워크북 Word 생성 (Type1: 테이블, Type2: 문단)
│   ├── models/
│   │   └── schemas.py              # Pydantic 데이터 모델
│   └── utils/
├── templates/
│   └── index.html                  # 메인 페이지 (탭 UI: 단어장 + 워크북)
├── static/
│   ├── css/style.css               # UI 스타일링 (탭 네비게이션 포함)
│   └── js/
│       ├── main.js                 # 탭 전환 + 단어장 탭 로직 (IIFE)
│       └── workbook.js             # 워크북 탭 로직 (IIFE)
├── temp/                           # 생성된 Word 파일 임시 저장
├── 중국어단어장.docx                # 단어장 Word 템플릿 원본
├── .env                            # 환경변수 (API 키, AI_PROVIDER)
├── requirements.txt                # Python 의존성
├── run.bat                         # 로컬 실행 스크립트
├── Procfile                        # Render 배포 시작 명령
├── render.yaml                     # Render 배포 설정
└── .gitignore
```

---

## 7. 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                     브라우저 (Client)                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              탭 네비게이션 (단어장 | 워크북)              │ │
│  ├──────────────────────┬─────────────────────────────────┤ │
│  │     단어장 탭         │         워크북 탭                │ │
│  │  main.js (IIFE)      │    workbook.js (IIFE)           │ │
│  │  업로드→편집→생성     │    업로드→자동감지→편집→생성      │ │
│  └──────────┬───────────┴────────────┬────────────────────┘ │
└─────────────┼────────────────────────┼──────────────────────┘
              │                        │
   ┌──────────▼──────────┐  ┌─────────▼─────────────────────┐
   │ 단어장 API           │  │ 워크북 API                     │
   │ POST /api/upload     │  │ POST /api/workbook/upload      │
   │ POST /api/generate   │  │ POST /api/workbook/generate    │
   │ GET  /api/download/* │  │ GET  /api/workbook/download/*  │
   └──────────┬───────────┘  └─────────┬─────────────────────┘
              │                        │
   ┌──────────▼────────────────────────▼──────────────────────┐
   │                    FastAPI Server                          │
   │  ┌──────────────────┐  ┌───────────────────────────────┐ │
   │  │  ai_extractor.py │  │  word_generator.py            │ │
   │  │  - 단어 추출      │  │  (템플릿 기반 단어장)          │ │
   │  │  - 유형 자동감지   │  ├───────────────────────────────┤ │
   │  │  - 워크북 추출    │  │  workbook_generator.py        │ │
   │  │  (Anthropic/     │  │  - Type1: 동적 테이블          │ │
   │  │   OpenAI)        │  │  - Type2: 문단 형태            │ │
   │  └──────────────────┘  └───────────────────────────────┘ │
   └──────────────────────────────────────────────────────────┘
```

---

## 8. 데이터 모델 (`schemas.py`)

### 8.1 단어장 모델

```python
class WordEntry(BaseModel):
    chinese: str
    pinyin: str
    korean: str

class GenerateRequest(BaseModel):
    job_id: str
    words: list[WordEntry]
```

### 8.2 워크북 모델

```python
class WorkbookType1Entry(BaseModel):
    chinese: str
    pinyin: str
    meaning: str
    example: str = ""

class WorkbookType2Entry(BaseModel):
    speaker: str
    korean: str
    chinese_text: str

class WorkbookGenerateRequest(BaseModel):
    job_id: str
    workbook_type: str          # "type1" 또는 "type2"
    entries: list[dict]         # 유형에 따라 다른 dict 구조
```

---

## 9. AI 추출 상세 (`ai_extractor.py`)

### 9.1 공통 구조

- 이미지를 Base64로 인코딩하여 AI Vision API에 전달
- 프롬프트로 JSON 형식 응답을 강제
- 응답에서 정규식(`\{.*\}`, `re.DOTALL`)으로 JSON 추출 후 파싱
- `AI_PROVIDER` 환경변수로 Anthropic(`claude-sonnet-4-5-20250929`) / OpenAI(`gpt-4o`) 전환
- 기본값: `anthropic`

### 9.2 워크북 AI 호출 흐름

**현재 (통합 방식):** 이미지당 1회 호출 + 병렬 처리
```
이미지 N장 업로드
    ↓
asyncio.gather(
    detect_and_extract_workbook(img1),   ← WORKBOOK_COMBINED_PROMPT (max_tokens=4096)
    detect_and_extract_workbook(img2),
    ...
)
    ↓
각 결과에서 type 확인 → type1_entries / type2_entries에 분류
```

> **레거시 (코드 유지, 미사용):** `detect_workbook_type()` → `extract_workbook()` 순차 2회 호출

### 9.3 프롬프트 목록

| 프롬프트 | 용도 | 응답 형식 |
|----------|------|-----------|
| `EXTRACT_PROMPT` | 단어장: 단어 추출 | `{"words": [...]}` |
| `WORKBOOK_COMBINED_PROMPT` | 워크북: 유형 판별 + 데이터 추출 (통합) | `{"type": "type1\|type2", "entries": [...]}` |
| `WORKBOOK_DETECT_PROMPT` | (레거시) 워크북: 유형 판별 | `{"type": "type1"}` |
| `WORKBOOK_TYPE1_PROMPT` | (레거시) 워크북 Type1: 테이블 데이터 추출 | `{"entries": [...]}` |
| `WORKBOOK_TYPE2_PROMPT` | (레거시) 워크북 Type2: 대화 데이터 추출 | `{"entries": [...]}` |

---

## 10. 프론트엔드 상세

### 10.1 탭 전환 (`main.js` 상단)

```javascript
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        // .tab-btn의 active 토글
        // #tab-{data-tab}의 active 토글
    });
});
```

### 10.2 단어장 탭 (`main.js` IIFE)

- 모든 DOM 요소 ID: `vocab-` 접두사 (예: `vocab-drop-zone`, `vocab-extract-btn`)
- API: `POST /api/upload` → `POST /api/generate` → `GET /api/download/{id}`
- 결과 테이블: `<input type="text">` 기반 인라인 편집

### 10.3 워크북 탭 (`workbook.js` IIFE)

- 모든 DOM 요소 ID: `wb-` 접두사 (예: `wb-drop-zone`, `wb-extract-btn`)
- API: `POST /api/workbook/upload` → `POST /api/workbook/generate` → `GET /api/workbook/download/{id}`
- 업로드 응답에서 `type1_entries`와 `type2_entries`를 분리 처리
- 두 유형이 동시에 있으면 두 결과 섹션 모두 표시
- 각 유형별 독립적인 행 추가/삭제/편집/생성 버튼

### 10.4 CSS 구조 (`style.css`)

- `.tab-nav` / `.tab-btn` / `.tab-content`: 탭 UI
- `.upload-area` / `.file-list` / `.file-tag`: 파일 업로드 영역
- `.result-table`: 결과 편집 테이블 (양 탭 공유)
- `.spinner`: 로딩 애니메이션
- `.delete-btn`: 행 삭제 버튼

---

## 11. 환경변수

| 변수 | 설명 | 예시 |
|------|------|------|
| `AI_PROVIDER` | AI 서비스 선택 (기본: `anthropic`) | `openai` 또는 `anthropic` |
| `OPENAI_API_KEY` | OpenAI API 키 | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API 키 | `sk-ant-...` |

---

## 12. 배포

### 12.1 로컬 실행

```bash
# run.bat 실행 (Windows)
# - 기존 Python 프로세스 종료
# - 포트 8000 사용 여부 확인
# - __pycache__ 정리
# - uvicorn 서버 시작
run.bat
```

### 12.2 Render 배포

1. GitHub 저장소에 push
2. Render 대시보드에서 `render.yaml` 기반 자동 배포
3. 환경변수 `ANTHROPIC_API_KEY` (또는 `OPENAI_API_KEY`)를 Render 대시보드에서 설정
4. 배포 URL: https://chinese-vocabook.onrender.com/

---

## 13. 비기능 요구사항

| 구분 | 내용 |
|------|------|
| AI 제공자 전환 | 환경변수(`AI_PROVIDER`)로 OpenAI/Anthropic 전환 가능 |
| 클라우드 배포 | Render 무료 티어로 배포 (15분 미사용 시 슬립, 콜드 스타트 지연) |
| 에러 처리 | 글로벌 예외 핸들러 + API별 에러 응답 (HTTPException, JSONResponse) |
| 멀티 유저 | 여러 사용자가 동시에 접속하여 사용 가능 (job_id 기반 파일 분리) |

---

## 14. 해결된 이슈

| 이슈 | 원인 | 해결 |
|------|------|------|
| Python 실행 안됨 | Windows Store 스텁 python.exe | `C:\Python313\python.exe` 직접 지정 |
| 콘솔 한자 깨짐 (cp949) | Windows 기본 인코딩 | 코스메틱 이슈, 기능에 영향 없음 |
| 브라우저 Internal Server Error | 좀비 프로세스가 포트 8000 점유 | `run.bat`에서 기존 프로세스 강제 종료 |
| Port 8000 바인드 에러 | taskkill 후 포트 해제 지연 | `timeout /t 3` 대기 + 포트 확인 로직 추가 |
| "body stream already read" JS 에러 | `res.json()` 실패 후 `res.text()` 재호출 | `res.text()` 먼저 읽고 `JSON.parse()` |
| GitHub 403 권한 에러 | 계정 불일치 (hshwang77 vs hhs486-sudo) | remote URL에 사용자명 포함 |
| 워크북 예문 누락 | AI가 일부 예문을 추출하지 않음 | 프롬프트 강화: "예문이 이미지에 있는데 누락하지 마세요" |
| Type 2 대화 간 빈 줄 | Word 문단 기본 spacing | `space_before=Pt(0)`, `space_after=Pt(0)` 설정 |
| 워크북 유형 감지 오류 | `detect_workbook_type` 함수 중복 정의 | 중복 함수 제거, 올바른 `_detect_type_*` 함수 사용 |
| 워크북 추출 속도 느림 | 이미지당 AI 2회 호출 + 순차 처리 | 통합 프롬프트 (1회 호출) + `asyncio.gather` 병렬 처리 |
| 두 유형 동시 추출 시 다운로드 후 복귀 불가 | 다운로드 화면에서 결과로 돌아가는 수단 없음 | "추출 결과로 돌아가기" 버튼 추가 (데이터 보존) |
| 병음 없는 테이블에서 한자 컬럼에 한국어 혼입 | 통합 프롬프트가 병음 없는 테이블 형식 미지원 | chinese 필드 한국어 금지 명시, 병음 자동 생성 지시, 의미 2개+예문 분리 규칙 추가 |

---

## 15. 향후 개선 사항 (미구현)

- [ ] 사용자 인증/로그인
- [ ] 추출 이력 저장 및 조회
- [ ] 임시 파일 자동 정리 (스케줄러)
- [ ] 이미지 미리보기
- [ ] PDF 출력 지원
- [ ] 모바일 UI 최적화
