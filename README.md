# 🛒 Seoul Local Market Analysis (Remake)

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.41-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.2-150458?style=flat&logo=pandas&logoColor=white)
![Tests](https://img.shields.io/badge/tests-pytest-0A9EDC?style=flat&logo=pytest&logoColor=white)

서울시 열린데이터 광장 API로 상권 데이터를 **수집 → 전처리 → 분석 → 시각화**하는 End-to-End 데이터 파이프라인 및 Streamlit 대시보드입니다.

> 이 저장소는 기존 `seoul-local-market-analysis` 프로젝트의 **리메이크 버전**으로,
> 단일 `app.py`에 몰려 있던 로직을 모듈화하고, 보안(.env)·데이터 관리·테스트·UI를 개선했습니다.

---

## 📊 이 시각화로 무엇을 알 수 있나 (Insights)

대시보드의 핵심은 **점포 수(STOR_CO)** 와 분기 내 **개업(OPBIZ)·폐업(CLSBIZ)** 흐름을
업종·자치구 단위로 교차 분석하는 것입니다. 단순 통계를 넘어 다음과 같은 **의사결정용 인사이트**를 얻을 수 있습니다.

<!-- AUTO-INSIGHTS:START -->

> 📂 아래 수치는 **실제 수집 데이터에서 자동 생성**되었습니다 — 분기 `20261`, 점포 **75,972행** · 100개 업종 · 25개 자치구 · 1650개 상권. _(생성: 2026-06-08 14:44, `python -m src.report`)_

### 1. 성장하는 업종 vs 쇠퇴하는 업종 — "지금 뜨는 시장 / 지는 시장"

분기 내 **순증감(개업 − 폐업)** 으로 시장의 진입·철수 방향을 읽을 수 있습니다.

| 순증가 상위 (성장) | 개업 | 폐업 | 순증 | | 순감소 상위 (쇠퇴) | 개업 | 폐업 | 순증 |
|---|--:|--:|--:|---|---|--:|--:|--:|
| 피부관리실 | 429 | 237 | **+192** | | 일반의류 | 390 | 1,186 | **−796** |
| 슈퍼마켓 | 318 | 218 | **+100** | | 전자상거래업 | 6 | 681 | **−675** |
| DVD방 | 101 | 16 | **+85** | | 부동산중개업 | 18 | 519 | **−501** |

→ **인사이트:** 이번 분기 순증 1위는 **피부관리실**(+192), 순감소 1위는 **일반의류**(−796). 신규 창업·투자라면 순증 업종에, 리스크 관리라면 순감소 업종에 주목하게 됩니다.

### 2. 창업 리스크 — "여긴 들어가면 위험한 시장인가"

점포 수 대비 폐업 비중(**폐업률**)으로 업종의 생존 난이도를 가늠합니다. (점포 500개 이상 업종 대상)

| 업종 | 점포 수 | 폐업 | 폐업률 |
|---|--:|--:|--:|
| 치킨전문점 | 1,613 | 155 | **9.6%** |
| 편의점 | 1,735 | 151 | **8.7%** |
| 패스트푸드점 | 2,360 | 204 | **8.6%** |

→ **인사이트:** 진입장벽이 낮은 프랜차이즈형 업종일수록 회전율(폐업률)이 높음 → **과당경쟁·포화 신호**.

### 3. 입지/경쟁 강도 — "이 업종은 어느 자치구에 집중되나"

특정 업종을 선택하면 자치구별 점포 분포와 개·폐업이 한눈에 비교됩니다. 예: **커피-음료**

| 자치구 | 점포 수 | 개업 | 폐업 | 순증 |
|---|--:|--:|--:|--:|
| 강남구 | 1,709 | 61 | 78 | **−17** |
| 마포구 | 1,644 | 68 | 104 | **−36** |
| 종로구 | 1,277 | 52 | 46 | **+6** |

→ **인사이트:** **강남구**는 점포가 가장 많지만 폐업이 개업을 초과(포화·경쟁 심화) — "점포가 많다 = 좋은 입지"가 아니라 **밀집도와 순증감을 함께 봐야** 한다는 점을 보여줍니다.

<!-- AUTO-INSIGHTS:END -->

### 4. 활용 시나리오

- **창업 예정자:** 순증 업종 + 순증 자치구의 교집합에서 후보 입지 탐색, 폐업률 높은 조합 회피.
- **상권 분석/컨설팅:** 업종별 성장·쇠퇴 랭킹으로 시장 리포트 자동화.
- **정책/투자:** 폐업 우위 지역을 소상공인 지원·모니터링 우선순위로 식별.
- **데이터 엔지니어링 관점:** 분기 스냅샷을 누적하면 **시계열 트렌드 센싱**으로 확장 가능(향후 과제).

> ⚠️ 현재 수집본은 **단일 분기 스냅샷**이라 개·폐업은 "추세"가 아닌 "해당 분기 흐름"입니다.
> 여러 분기를 누적 적재하면 성장 곡선·계절성까지 분석할 수 있습니다.

---

## ✨ 리메이크에서 개선한 점

| 영역 | Before | After |
|---|---|---|
| 구조 | `app.py`에 로딩·필터·집계·시각화 혼재 | `src/` 패키지로 책임 분리 |
| API 키 | 실행 가능한 `config.py`에 평문 저장 | `.env` + `python-dotenv` |
| 수집 안정성 | 타임아웃·재시도 없음 | 타임아웃 + 지수 백오프 재시도 |
| 데이터 관리 | 33MB CSV가 Git에 추적됨 | raw/processed는 Git 제외, 소형 샘플만 포함 |
| 데모 실행 | 전처리된 CSV 필수 | 키·데이터 없이 **샘플로 즉시 실행** |
| 테스트 | 없음 | `pytest` 단위 테스트 |

---

## 🔬 코드 레벨 비교 분석 (Before → After)

기존 프로젝트의 실제 코드를 기준으로, 어떤 장단점이 있었고 리메이크에서 무엇을 바꿨는지 정리했습니다.

### 1. API 키 관리 — `config.py` import + `sys.path` 조작 → `.env`

**Before** (`src/collector.py`)

```python
# 현재 파일의 부모의 부모 폴더(루트)를 sys.path 에 추가하고 config 를 import
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

try:
    from config import SEOUL_API_KEY
except ImportError:
    print("[ERROR] config.py 파일을 찾을 수 없습니다. API 키 설정이 필요합니다.")
    SEOUL_API_KEY = ""
```

- 👍 **장점**: 키를 소스에 하드코딩하지 않고 `config.py`(gitignore)로 분리한 점은 좋았습니다.
- 👎 **단점**: 키를 *실행 가능한 파이썬 파일*에 저장해 import 시 부작용 위험이 있고, `sys.path`를 런타임에 조작하며, 동일 블록이 `collector.py`/`preprocessor.py`에 **그대로 중복**되었습니다. `config.py`를 손수 만들어야 해 진입 장벽도 컸습니다.

**After** (`src/config.py`)

```python
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")  # 없어도 조용히 통과 → 샘플 데모는 키 없이 동작

SEOUL_API_KEY = os.getenv("SEOUL_API_KEY", "").strip()
_PLACEHOLDERS = {"", "YOUR_ACCESS_KEY_HERE", "여기에_인증키를_입력하세요"}

def has_valid_api_key() -> bool:
    return SEOUL_API_KEY not in _PLACEHOLDERS
```

- 🔧 **보완**: 표준 `.env` 방식으로 전환하고, 키 검증 로직을 한곳에 모았습니다. 키가 없어도 예외 없이 통과하여 샘플 데모가 가능합니다.

---

### 2. 데이터 수집 — 타임아웃·재시도 없는 중복 페이지네이션 → 공통 수집기

**Before** (`src/collector.py`)

```python
while True:
    end_index = start_index + BATCH_SIZE - 1
    url = f"http://openapi.seoul.go.kr:8088/{KEY}/{TYPE}/{SERVICE}/{start_index}/{end_index}/"
    try:
        response = requests.get(url)               # ❌ 타임아웃 없음 / ❌ 재시도 없음
        if response.status_code != 200:
            print(f"[ERROR] API 호출 실패: {response.status_code}")
            break
        data = response.json()
        ...
    except Exception as e:
        print(f"[ERROR] 프로세스 실행 중 예외 발생: {e}")
        break
```

- 👍 **장점**: 페이지네이션과 마지막 페이지 판정, 기본 예외 처리가 구현되어 있었습니다.
- 👎 **단점**: `requests.get`에 **타임아웃이 없어** 네트워크 지연 시 무한 대기 가능, **재시도 없음**으로 일시적 오류에 취약, 키가 URL 경로에 그대로 들어가 **로그 노출 위험**. 동일한 `while` 페이지네이션 루프가 `preprocessor.py`에도 **복사되어 중복**되었습니다.

**After** (`src/utils.py`)

```python
def fetch_json(url: str) -> Dict[str, Any]:
    last_exc = None
    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            resp = requests.get(url, timeout=config.REQUEST_TIMEOUT)  # ✅ 타임아웃
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as exc:        # ✅ 재시도
            last_exc = exc
            time.sleep(config.RETRY_BACKOFF * attempt)                # ✅ 지수 백오프
            logger.warning("요청 실패(%s/%s): %s", attempt, config.MAX_RETRIES, _mask_key(url))
    raise RuntimeError(f"API 요청이 {config.MAX_RETRIES}회 모두 실패했습니다: {last_exc}")

def paginate(service: str, limit=None):       # ✅ 수집/전처리가 공유하는 단일 구현
    ...
```

- 🔧 **보완**: 타임아웃·재시도·백오프를 갖춘 단일 HTTP 헬퍼와 공통 `paginate()`로 **중복을 제거**하고, 로그에서는 `_mask_key()`로 키를 가립니다.

---

### 3. 대시보드 — 단일 `app.py`에 모든 로직 집중 → 모듈 분리

**Before** (`app.py`)

```python
# 로딩 · 필터 · 집계 · 시각화가 한 파일에 절차적으로 섞여 있음
df = pd.read_csv(os.path.join("data", "seoul_market_final.csv"))
filtered_df = df[df['SVC_INDUTY_CD_NM'] == selected_industry]
district_group = filtered_df.groupby('SIGNGU_CD_NM')[['OPBIZ_STOR_CO', 'CLSBIZ_STOR_CO']].sum()...
fig = px.bar(district_melted, x='SIGNGU_CD_NM', y='Count', color='Status', ...)

# 서버 강제 종료 버튼
if st.sidebar.button("❌ 앱 종료 (Server Stop)"):
    os.kill(os.getpid(), signal.SIGTERM)        # ⚠️ 배포 환경에서 위험
```

- 👍 **장점**: Streamlit + Plotly로 인터랙티브 필터/KPI/차트를 빠르게 구현했습니다.
- 👎 **단점**: 데이터 로딩·필터·집계·시각화가 한 파일에 절차적으로 섞여 **테스트 불가**하고 변경 시 회귀 위험이 큽니다. 컬럼명 매직 스트링이 곳곳에 흩어져 있고, `os.kill`로 서버를 강제 종료하는 버튼은 Streamlit Cloud 등 배포 환경에서 위험/불필요합니다.

**After** (`app.py` — UI 조립만, 로직은 순수 함수에 위임)

```python
from src import charts, data_loader, metrics

df, source = get_data()                                  # data_loader 가 샘플 폴백까지 처리
filtered = metrics.filter_data(df, industry=selected_industry, districts=selected_districts)
kpi = metrics.compute_kpi(filtered)                      # 순수 함수 → 테스트 가능
district_df = metrics.aggregate_by_district(filtered)
fig = charts.district_open_close_bar(district_df, title=...)
# os.kill 종료 버튼 제거
```

- 🔧 **보완**: 계산은 `metrics`(순수 함수), 시각화는 `charts`, 로딩은 `data_loader`로 분리해 **단위 테스트가 가능**해졌고, 컬럼명은 `config.COLS`로 중앙화했으며, 위험한 종료 버튼을 제거했습니다.

---

### 4. 전처리 — I/O와 변환이 한 함수에 결합 → 순수 함수로 분리

**Before** (`src/preprocessor.py`) — `merge_location_data()` 하나가 키 검증·파일 읽기·API 수집·병합·저장을 모두 수행하여 테스트할 수 없었습니다.

**After** (`src/preprocessor.py`)

```python
def clean_numeric(df, columns=config.NUMERIC_COLS):   # 입력 DataFrame → 출력 DataFrame
    ...
def build_dimension(location_df):                     # 순수 함수 (I/O 없음)
    ...
def merge_market_data(store_df, location_df):         # 순수 함수 → pytest 로 검증
    ...
def run():                                             # 파일 I/O 는 여기서만
    ...
```

- 🔧 **보완**: 변환 로직을 입출력이 명확한 순수 함수로 분리하고, 결측 자치구는 `Unknown` 처리, 수치형은 `to_numeric(errors="coerce")`로 강제 변환해 집계 안정성을 높였습니다. `tests/test_preprocessor.py`로 검증합니다.

---

### 5. 데이터 거버넌스 — 33MB CSV가 Git에 추적됨 → 샘플만 포함

**Before** (`.gitignore`)

```gitignore
*.csv
data/*.csv
```

- 👎 **단점**: `.gitignore`에 `*.csv`가 있었지만 `data/seoul_market_final.csv`(33MB, 30만 행)는 **이미 추적된 뒤라 무시되지 않아** 저장소에 그대로 커밋되어 있었습니다(저장소 비대). 또한 CSV가 없으면 대시보드를 실행조차 할 수 없었습니다.

**After** (`.gitignore` + `data_loader.py`)

```gitignore
data/raw/*
data/processed/*
!data/raw/.gitkeep
!data/processed/.gitkeep
!data/sample/        # 소형 데모 샘플만 추적
```

```python
def resolve_data_path():
    if config.PROCESSED_FILE.exists():
        return config.PROCESSED_FILE, "processed"
    if config.SAMPLE_FILE.exists():
        return config.SAMPLE_FILE, "sample"   # 키·대용량 데이터 없이도 데모 가능
    return None, "none"
```

- 🔧 **보완**: 대용량 raw/processed는 추적에서 제외하고 소형 샘플(600행, 68KB)만 포함해, 누구나 클론 즉시 대시보드를 체험할 수 있습니다. 실제 대용량 데이터는 로컬/Nextcloud에서 관리합니다.

---

## 📂 프로젝트 구조

```text
seoul-local-market-remake/
├── app.py                  # Streamlit 진입점 (UI 조립만 담당)
├── requirements.txt
├── .env.example            # API 키 템플릿
├── .gitignore
├── data/
│   ├── raw/                # 수집 원본 (Git 제외)
│   ├── processed/          # 전처리 결과 (Git 제외)
│   └── sample/             # 데모용 소형 샘플 (Git 포함)
├── src/
│   ├── config.py           # .env 로드 + 경로/서비스/컬럼 상수
│   ├── utils.py            # 로깅 + 재시도 HTTP + 페이지네이션
│   ├── collector.py        # API 수집 → data/raw
│   ├── preprocessor.py     # 병합/정제 (순수 함수) → data/processed
│   ├── data_loader.py      # 캐싱 로더 + 샘플 폴백
│   ├── metrics.py          # KPI/집계 (순수 함수)
│   ├── charts.py           # Plotly 차트
│   └── report.py           # README 인사이트 자동 생성/주입
├── tests/
│   ├── test_preprocessor.py
│   ├── test_metrics.py
│   └── test_report.py
└── docs/
    └── project_notes.md
```

---

## 🚀 실행 방법

### 1. 환경 설정

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 대시보드 실행 (키 없이 바로 데모)

```bash
streamlit run app.py
```

전처리된 데이터가 없으면 자동으로 `data/sample/`의 샘플 데이터로 실행됩니다.

### 3. 실제 데이터 수집 (선택)

`.env`에 [서울 열린데이터 광장](https://data.seoul.go.kr/) 인증키를 설정합니다.

```bash
cp .env.example .env          # 편집하여 SEOUL_API_KEY 입력
                              # (선택) TARGET_QUARTER=20261 로 특정 분기만 수집
python -m src.collector       # 수집 → data/raw/
python -m src.preprocessor    # 전처리 → data/processed/ (+ README 인사이트 자동 갱신)
streamlit run app.py          # 전체 데이터로 실행
```

> 📊 위 **`📊 Insights`** 섹션의 표·수치는 전처리 시 현재 데이터 기준으로 **자동 갱신**됩니다.
> 데이터는 그대로 두고 문서만 다시 만들려면 `python -m src.report` 를 실행하세요.

### 4. 테스트

```bash
pytest
```

---

## 🔐 보안 / 데이터 정책

- API 키는 코드에 하드코딩하지 않고 **`.env`** 로만 관리합니다(`.gitignore` 처리).
- 대용량 원본/가공 CSV(`data/raw`, `data/processed`)는 **Git에 올리지 않으며**, 로컬 또는 Nextcloud에서 관리합니다.
- 저장소에는 키 없이도 동작을 확인할 수 있는 **소형 샘플 데이터만** 포함합니다.

---

## 🧱 데이터 모델 (Star Schema)

- **Fact**: `VwsmTrdarStorQq` (상권-점포: 점포 수, 개업/폐업 수)
- **Dimension**: `TbgisTrdarRelm` (상권 영역 → 자치구 `SIGNGU_CD_NM`)
- **Join Key**: `TRDAR_CD` (상권 코드)
