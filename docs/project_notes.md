# 프로젝트 노트 (설계 의사결정)

## 1. 왜 리메이크인가

기존 `seoul-local-market-analysis`는 동작은 하지만 다음 문제가 있었다.

- 모든 로직이 `app.py`에 절차적으로 집중되어 변경/테스트가 어려움.
- API 키를 실행 가능한 `config.py`에 평문 저장(import 부작용 위험).
- 수집/전처리에 페이지네이션 로직이 중복, 타임아웃·재시도 부재.
- 33MB CSV가 Git에 추적되어 저장소가 비대.
- 테스트가 전무.

기능을 보존하면서 구조와 실행 안정성을 개선하는 것이 목표.

## 2. 아키텍처

```
app.py (UI)
  └─ src.data_loader ─ src.metrics ─ src.charts
src.collector ─┐
src.preprocessor ┴─ src.utils ─ src.config (.env)
```

- **순수 함수 우선**: `metrics`, `preprocessor`의 변환 함수는 I/O 없이 동작 → pytest로 검증.
- **UI는 얇게**: `app.py`는 데이터 조립과 위젯 배치만 담당.
- **상수 중앙화**: 서비스명·컬럼명·경로를 `config.py`에 모아 매직값 제거.

## 3. 데이터 흐름

1. `collector` → `data/raw/seoul_market_store.csv`, `seoul_market_location.csv`
2. `preprocessor` → Left Join + 수치 정제 → `data/processed/seoul_market_final.csv`
3. `data_loader` → processed 우선, 없으면 `data/sample/`로 폴백

## 4. 보안 / 데이터 거버넌스

- 키는 `.env` 전용. `utils.fetch_json`는 로그에서 키를 마스킹.
- `.gitignore`로 raw/processed CSV 추적 차단, 샘플만 허용.
- 대용량 원본은 로컬/Nextcloud 보관.

## 5. 안정성 개선

- HTTP: `REQUEST_TIMEOUT`, `MAX_RETRIES`, 지수 백오프.
- 결측 자치구는 `Unknown`으로 채워 집계 깨짐 방지.
- 수치형 컬럼은 `to_numeric(errors="coerce")`로 강제 변환.

## 6. 향후 과제

- 위치 차원 데이터 캐싱(전처리 시 raw 재사용).
- 시계열(분기 `STDR_YYQU_CD`) 추세 시각화 추가.
- CI에서 pytest 자동 실행.
- 데이터 정합성 검증(스키마/행수) 단계 추가.
