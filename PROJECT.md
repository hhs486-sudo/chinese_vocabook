# 중국어 단어장 생성기 (Chinese Vocab Generator)

## 1. 프로젝트 개요

사진에서 중국어(한자), 병음(Pinyin), 한국어 뜻을 AI로 추출하여 MS Word 기반 단어장을 자동 생성하는 웹 서비스.

- **URL (배포)**: https://chinese-vocabook.onrender.com/
- **GitHub**: https://github.com/hhs486-sudo/chinese_vocabook
- **로컬 실행**: `run.bat` 실행 후 http://localhost:8000 접속

---

## 2. 요구사항

### 2.1 기능 요구사항

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
| 파일 다운로드 | 생성된 `.docx` 파일을 브라우저에서 다운로드 |
| 멀티 유저 | 여러 사용자가 동시에 접속하여 사용 가능 |

### 2.2 비기능 요구사항

| 구분 | 내용 |
|------|------|
| AI 제공자 전환 | 환경변수(`AI_PROVIDER`)로 OpenAI/Anthropic 전환 가능 |
| 클라우드 배포 | Render 무료 티어로 배포 (15분 미사용 시 슬립, 콜드 스타트 지연) |
| 에러 처리 | 글로벌 예외 핸들러 + API별 에러 응답 |

### 2.3 입력 데이터 형식

사진 속 텍스트는 다음 형식을 따름:

```
*打扫 [dǎsǎo] 청소하다
检查 [jiǎnchá] 검사하다
```

- 각 줄: `한자 [병음] 한글뜻` (공백으로 구분)
- `*` 접두사: 제거 대상
- `[]` 내부: 병음 (성조 포함)
- 병음 뒤 한글: 한국어 뜻

---

## 3. 기술 스택

| 항목 | 기술 |
|------|------|
| 백엔드 | Python 3.13 + FastAPI |
| ASGI 서버 | Uvicorn |
| AI (기본) | OpenAI GPT-4o Vision API |
| AI (대체) | Anthropic Claude Sonnet 4.5 |
| Word 처리 | python-docx |
| 프론트엔드 | HTML + CSS + JavaScript (Jinja2 템플릿) |
| 배포 | Render (Free Tier) |
| 소스 관리 | GitHub |

### 3.1 의존성 (requirements.txt)

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

## 4. 시스템 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                    브라우저 (Client)                   │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │ 이미지    │  │ 결과편집  │  │ Word 다운로드     │  │
│  │ 업로드    │→ │ 테이블   │→ │                   │  │
│  └──────────┘  └──────────┘  └───────────────────┘  │
└────────┬──────────────┬──────────────┬──────────────┘
         │              │              │
    POST /api/upload  POST /api/generate  GET /api/download/{id}
         │              │              │
┌────────▼──────────────▼──────────────▼──────────────┐
│                  FastAPI Server                       │
│  ┌──────────────┐  ┌────────────────────────────┐   │
│  │ ai_extractor  │  │ word_generator             │   │
│  │ (OpenAI/     │  │ (python-docx 템플릿 채우기) │   │
│  │  Anthropic)  │  │                            │   │
│  └──────┬───────┘  └────────────┬───────────────┘   │
│         │                       │                    │
│    AI Vision API          중국어단어장.docx 템플릿    │
└──────────────────────────────────────────────────────┘
```

---

## 5. 프로젝트 구조

```
china_book/
├── app/
│   ├── main.py                 # FastAPI 앱 진입점, 글로벌 예외 핸들러
│   ├── api/
│   │   └── routes.py           # API 엔드포인트 (upload, generate, download)
│   ├── services/
│   │   ├── ai_extractor.py     # AI 이미지 텍스트 추출 (OpenAI/Anthropic)
│   │   └── word_generator.py   # Word 파일 생성 (템플릿 기반)
│   ├── models/
│   │   └── schemas.py          # Pydantic 데이터 모델
│   └── utils/
├── templates/
│   └── index.html              # 메인 페이지 (Jinja2)
├── static/
│   ├── css/style.css           # UI 스타일링
│   └── js/main.js              # 프론트엔드 로직 (업로드, 편집, 생성)
├── temp/                       # 생성된 Word 파일 임시 저장
├── 중국어단어장.docx            # Word 템플릿 원본
├── .env                        # 환경변수 (API 키, AI_PROVIDER)
├── requirements.txt            # Python 의존성
├── run.bat                     # 로컬 실행 스크립트
├── Procfile                    # Render 배포 시작 명령
├── render.yaml                 # Render 배포 설정
└── .gitignore
```

---

## 6. API 명세

### 6.1 POST `/api/upload`

이미지 파일을 업로드하고 AI로 중국어 단어를 추출한다.

- **Request**: `multipart/form-data` — `files` (다중 이미지)
- **Response**:
  ```json
  {
    "job_id": "uuid",
    "words": [
      {"chinese": "打扫", "pinyin": "dǎsǎo", "korean": "청소하다"},
      ...
    ]
  }
  ```
- **에러**: 400 (파일 없음/비이미지), 500 (서버 오류)

### 6.2 POST `/api/generate`

편집된 단어 목록으로 Word 파일을 생성한다.

- **Request**:
  ```json
  {
    "job_id": "uuid",
    "words": [
      {"chinese": "打扫", "pinyin": "dǎsǎo", "korean": "청소하다"}
    ]
  }
  ```
- **Response**:
  ```json
  {"download_id": "file-uuid"}
  ```

### 6.3 GET `/api/download/{download_id}`

생성된 Word 파일을 다운로드한다.

- **Response**: `중국어단어장.docx` 파일 (application/vnd.openxmlformats)

---

## 7. 핵심 구현 상세

### 7.1 AI 이미지 추출 (`ai_extractor.py`)

- 이미지를 Base64로 인코딩하여 AI Vision API에 전달
- 프롬프트로 JSON 형식 응답을 강제
- 응답에서 정규식(`\{.*\}`)으로 JSON 추출 후 파싱
- `AI_PROVIDER` 환경변수로 OpenAI(`gpt-4o`) / Anthropic(`claude-sonnet-4-5`) 전환

### 7.2 Word 생성 (`word_generator.py`)

- 템플릿 파일(`중국어단어장.docx`)을 열고 Row 0부터 데이터 삽입 (헤더 행 없음)
- **테이블 구조**: 1개 테이블, 29행 (모두 데이터), 6열
- **셀 매핑**: `cells[0]` = 한자, `cells[3]` = 병음, `cells[5]` = 뜻
- **폰트 설정**: 한자 `Microsoft YaHei 12pt` (eastAsia 폰트 명시), 병음 `맑은 고딕 12pt`, 뜻 `맑은 고딕 11pt`
- **자동 폰트 축소**: 뜻 텍스트의 너비를 계산하여 셀에 한 줄로 들어가도록 폰트 크기 자동 조절
  - Full-width 문자 (한글, 한자) = 1.0 width unit
  - Half-width 문자 (ASCII, 공백, 구두점) = 0.5 width unit
  - 사용 가능 너비 = 셀 너비 - 셀 패딩 (모두 템플릿 XML에서 동적 읽기)
- **다중 페이지**: 단어 수 초과 시 템플릿 테이블 XML을 통째로 복제하여 동일 구조 유지
- **동적 템플릿 읽기**: 행 수, 셀 너비, 셀 패딩을 모두 템플릿에서 런타임 읽기 (하드코딩 없음)

### 7.3 프론트엔드 (`main.js`)

- 드래그 앤 드롭 + 클릭 파일 선택
- 추출 결과를 편집 가능한 테이블로 표시
- 인라인 편집: 셀 클릭 시 `contenteditable`로 전환
- 행 추가/삭제 버튼
- Word 생성 후 자동 다운로드 링크 제공

---

## 8. 환경변수

| 변수 | 설명 | 예시 |
|------|------|------|
| `AI_PROVIDER` | AI 서비스 선택 | `openai` 또는 `anthropic` |
| `OPENAI_API_KEY` | OpenAI API 키 | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API 키 | `sk-ant-...` |

---

## 9. 배포

### 9.1 로컬 실행

```bash
# run.bat 실행 (Windows)
# - 기존 Python 프로세스 종료
# - 포트 8000 사용 여부 확인
# - __pycache__ 정리
# - uvicorn 서버 시작
run.bat
```

### 9.2 Render 배포

1. GitHub 저장소에 push
2. Render 대시보드에서 `render.yaml` 기반 자동 배포
3. 환경변수 `OPENAI_API_KEY`를 Render 대시보드에서 설정
4. 배포 URL: https://chinese-vocabook.onrender.com/

---

## 10. 해결된 이슈

| 이슈 | 원인 | 해결 |
|------|------|------|
| Python 실행 안됨 | Windows Store 스텁 python.exe | `C:\Python313\python.exe` 직접 지정 |
| 콘솔 한자 깨짐 (cp949) | Windows 기본 인코딩 | 코스메틱 이슈, 기능에 영향 없음 |
| 브라우저 Internal Server Error | 좀비 프로세스가 포트 8000 점유 | `run.bat`에서 기존 프로세스 강제 종료 |
| Port 8000 바인드 에러 | taskkill 후 포트 해제 지연 | `timeout /t 3` 대기 + 포트 확인 로직 추가 |
| "body stream already read" JS 에러 | `res.json()` 실패 후 `res.text()` 재호출 | `res.text()` 먼저 읽고 `JSON.parse()` |
| GitHub 403 권한 에러 | 계정 불일치 (hshwang77 vs hhs486-sudo) | remote URL에 사용자명 포함 |

---

## 11. 향후 개선 사항 (미구현)

- [ ] 사용자 인증/로그인
- [ ] 추출 이력 저장 및 조회
- [ ] 임시 파일 자동 정리 (스케줄러)
- [ ] 이미지 미리보기
- [ ] PDF 출력 지원
- [ ] 모바일 UI 최적화
