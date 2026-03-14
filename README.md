# 🀄 Lilly Youn의 중국어 학습 도우미

> 교재 사진을 찍으면 AI가 자동으로 MS Word 학습 자료를 만들어주는 웹 서비스

**배포 URL**: https://chinese-vocabook.onrender.com/

---

## 목차

1. [프로젝트 소개](#1-프로젝트-소개)
2. [주요 기능](#2-주요-기능)
3. [기술 스택](#3-기술-스택)
4. [프로젝트 구조](#4-프로젝트-구조)
5. [기능 상세](#5-기능-상세)
   - [단어장 탭](#51-단어장-탭)
   - [워크북 탭](#52-워크북-탭)
   - [한자 탭](#53-한자-탭)
6. [API 명세](#6-api-명세)
7. [환경 설정](#7-환경-설정)
8. [로컬 실행](#8-로컬-실행)
9. [배포](#9-배포)

---

## 1. 프로젝트 소개

EBS 중국어 교재 및 한문 교재 사진에서 AI(Vision API)로 텍스트를 추출하여 MS Word 학습 자료를 자동 생성하는 웹 서비스입니다.

- 교재 사진 → AI 추출 → 브라우저에서 편집 → Word 파일 다운로드
- 따라쓰기용 회색 한자, 단어장, 한자 훈/음 카드 등 다양한 학습 자료 생성
- Anthropic Claude Sonnet / OpenAI GPT-4o 중 선택하여 사용

---

## 2. 주요 기능

| 탭 | 기능 | 출력 |
|----|------|------|
| **단어장** | 사진에서 한자·병음·뜻 추출 | 중국어단어장.docx |
| **워크북** | 교재 유형 자동 감지 후 따라쓰기 워크북 생성 (4가지 유형) | 중국어워크북.docx |
| **한자** | 한문 교재에서 한자·훈·음 추출 | 한자단어장.docx |

---

## 3. 기술 스택

| 구분 | 기술 |
|------|------|
| 백엔드 | Python 3.13 + FastAPI + Uvicorn |
| AI (기본) | Anthropic Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`) |
| AI (대체) | OpenAI GPT-4o |
| Word 생성 | python-docx + lxml (XML 직접 조작) |
| 프론트엔드 | Vanilla JS + Jinja2 (프레임워크 없음) |
| 배포 | Render (Free Tier) |

---

## 4. 프로젝트 구조

```
lilly_chinese_work/
├── app/
│   ├── main.py                    # FastAPI 앱 진입점
│   ├── api/
│   │   └── routes.py              # API 엔드포인트 (단어장 + 워크북 + 한자)
│   ├── services/
│   │   ├── ai_extractor.py        # AI Vision API 추출 로직 (모든 프롬프트 포함)
│   │   ├── word_generator.py      # 단어장 / 한자 Word 생성
│   │   └── workbook_generator.py  # 워크북 Word 생성 (Type 1~4)
│   └── models/
│       └── schemas.py             # Pydantic 모델
├── templates/
│   └── index.html                 # 메인 페이지 (단어장 / 워크북 / 한자 탭)
├── static/
│   ├── css/style.css
│   └── js/
│       ├── main.js                # 탭 전환 + 단어장 로직 (IIFE)
│       ├── workbook.js            # 워크북 로직 (IIFE)
│       └── hanja.js               # 한자 로직 (IIFE)
├── 중국어단어장.docx               # 단어장 Word 템플릿
├── 한자단어장.docx                 # 한자 Word 템플릿
├── temp/                          # 생성된 Word 파일 임시 저장
├── requirements.txt
├── run.bat                        # 로컬 실행 스크립트 (Windows)
├── Procfile                       # Render 시작 명령
└── render.yaml                    # Render 배포 설정
```

---

## 5. 기능 상세

### 5.1 단어장 탭

EBS 중국어 교재 사진에서 한자·병음·뜻을 추출하여 Word 단어장을 생성합니다.

#### 지원 입력 형식

```
*打扫 [dǎsǎo] 청소하다          ← 괄호 있는 병음
哪儿 nǎr 어디                   ← 괄호 없는 병음 (교과서 형식)
矮 [ǎi] / 低 [dī] 작다          ← 반의어/동의어 쌍 → 2개 entry로 자동 분리
```

#### Word 출력 규격

- 템플릿(`중국어단어장.docx`) 기반, 29행 × 6열 테이블
- `cells[0]` = 한자 (Microsoft YaHei 12pt)
- `cells[3]` = 병음 (맑은 고딕 12pt)
- `cells[5]` = 뜻 (맑은 고딕 11pt, 셀 초과 시 자동 축소 최소 7pt)
- 단어 수 초과 시 동일 테이블 구조를 복제하여 다음 페이지 자동 생성

---

### 5.2 워크북 탭

교재 사진을 업로드하면 AI가 유형을 자동 감지(4종)하여 따라쓰기 워크북을 생성합니다.
회색(`#EAEAEA`) 한자 위에 직접 따라쓸 수 있도록 설계되었습니다.

이미지 1장당 **AI 1회 호출**로 유형 감지 + 데이터 추출을 동시에 처리하며, 여러 장은 `asyncio.gather`로 병렬 처리합니다.

#### 워크북 유형 4가지

| 유형 | 감지 기준 | Word 출력 구조 |
|------|-----------|----------------|
| **Type 1** (세로 테이블) | 표 형식 — 한자·병음·의미·예문이 행으로 나열 | 4열 테이블. 회색 한자/예문, 컬럼 너비 동적 계산 |
| **Type 2** (유형학습) | A:, B: 화자 대화 + 본문해석 섹션 분리 | 한국어 줄 → 회색 중국어 줄 (교대 반복) |
| **Type 3** (어구풀이) | 번호+굵은 헤더 + 불릿(•) 예문 쌍 나열 | 한국어 줄 → 회색 중국어 줄 (교대 반복) |
| **Type 4** (교과서 본문) | 한국어 번역 없는 순수 중국어 대화문 | AI가 한국어 번역 자동 생성 → 한국어 줄 → 회색 중국어 줄 |

#### Type 1 컬럼 너비 동적 계산

1. 전체 entry를 순회하여 한자·예문 컬럼의 최대 텍스트 너비(pt) 계산
2. CJK 문자 = `font_size`pt, ASCII 문자 = `font_size × 0.5`pt
3. 한자·예문 컬럼에 `noWrap` 설정 (1줄 고정)
4. 나머지 너비를 병음·의미 컬럼에 균등 배분 (2줄 허용)

#### 공통 폰트 규격

| 요소 | 폰트 | 크기 | 색상 |
|------|------|------|------|
| 중국어 한자 (따라쓰기) | Microsoft YaHei | 16pt | 회색 `#EAEAEA` |
| 한국어 해석 | 맑은 고딕 | 11pt | 검정 |
| 병음 | 맑은 고딕 | 11pt | 검정 |

---

### 5.3 한자 탭

한문 교재 사진에서 한자·훈·음을 추출하여 한자 단어장을 생성합니다.

#### 지원 입력 형식

```
山 산 산          → hanja: 山, hun: 산, eum: 산
金 쇠/성씨 금/김  → 복수 독음 슬래시 구분
```

#### Word 출력 규격

- 템플릿(`한자단어장.docx`) 기반
- `cells[0]` = 한자 (Microsoft YaHei 15pt, 검정)
- `cells[1]` = 한자 (Microsoft YaHei 15pt, 회색 `#EAEAEA` — 먹글자 따라쓰기용)
- `cells[2]` = 훈 / **음** (맑은 고딕 13pt, 음은 **굵게**)

---

## 6. API 명세

### 단어장

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/upload` | 이미지 → AI 단어 추출 |
| POST | `/api/generate` | 단어 목록 → Word 생성 |
| GET | `/api/download/{id}` | Word 파일 다운로드 |

### 워크북

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/workbook/upload` | 이미지 → 유형 자동 감지 + 데이터 추출 |
| POST | `/api/workbook/generate` | 데이터 → Word 워크북 생성 |
| GET | `/api/workbook/download/{id}` | Word 파일 다운로드 |

**POST `/api/workbook/upload` 응답:**
```json
{
  "job_id": "uuid",
  "type1_entries": [{"chinese": "向", "pinyin": "xiàng", "meaning": "~을 향하여", "example": "我向他借了一本书。"}],
  "type2_entries": [{"speaker": "A", "chinese_text": "你好！", "korean": "안녕하세요!"}],
  "type3_entries": [{"chinese_text": "你好！", "korean": "안녕하세요!"}],
  "type4_entries": [{"chinese_text": "你好！", "korean": "안녕하세요!"}]
}
```

### 한자

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/hanja/upload` | 이미지 → 한자·훈·음 추출 |
| POST | `/api/hanja/generate` | 추출 데이터 → Word 생성 |
| GET | `/api/hanja/download/{id}` | Word 파일 다운로드 |

---

## 7. 환경 설정

루트 디렉토리에 `.env` 파일을 생성합니다:

```env
AI_PROVIDER=anthropic          # anthropic 또는 openai (기본: anthropic)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...          # AI_PROVIDER=openai 시 사용
```

`.env` 파일은 절대 커밋하지 마세요 (`.gitignore`에 포함됨).

---

## 8. 로컬 실행

```bash
# Windows — run.bat 실행
# (기존 프로세스 종료 → __pycache__ 정리 → uvicorn 시작)
run.bat
```

또는 직접 실행:

```bash
C:\Python313\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

브라우저에서 http://localhost:8000 접속

---

## 9. 배포

GitHub에 push하면 Render에서 자동 배포됩니다.

1. Render 대시보드에서 환경변수 설정 (`ANTHROPIC_API_KEY` 등)
2. `render.yaml` 기반 자동 빌드 및 배포
3. 배포 후 접속: https://chinese-vocabook.onrender.com/

> **참고**: Render Free Tier는 15분 미사용 시 슬립 상태로 전환됩니다. 첫 접속 시 콜드 스타트 지연(약 30~60초)이 발생할 수 있습니다.
