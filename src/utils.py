"""공용 유틸리티: 로깅 설정과 재시도/타임아웃을 갖춘 HTTP 헬퍼."""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Iterator, List

import requests

from . import config

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def get_logger(name: str) -> logging.Logger:
    """모듈별 로거. 핸들러 중복 등록을 방지한다."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


logger = get_logger(__name__)


def _mask_key(url: str) -> str:
    """로그 출력 시 URL 경로에 포함된 API 키를 가린다."""
    key = config.SEOUL_API_KEY
    if key:
        return url.replace(key, "***")
    return url


def fetch_json(url: str) -> Dict[str, Any]:
    """단일 GET 요청 + 재시도. 실패 시 마지막 예외를 올린다."""
    last_exc: Exception | None = None
    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            resp = requests.get(url, timeout=config.REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as exc:
            last_exc = exc
            # 마지막 시도 실패 후에는 재시도가 없으므로 대기 없이 바로 raise 한다.
            if attempt < config.MAX_RETRIES:
                wait = config.RETRY_BACKOFF * attempt
                logger.warning(
                    "요청 실패(%s/%s): %s | %s초 후 재시도",
                    attempt, config.MAX_RETRIES, _mask_key(url), wait,
                )
                time.sleep(wait)
    raise RuntimeError(f"API 요청이 {config.MAX_RETRIES}회 모두 실패했습니다: {last_exc}")


# 서울 열린데이터 광장 RESULT 코드: 정상 / 데이터 없음(오류 아님)
_RESULT_OK = "INFO-000"
_RESULT_NO_DATA = "INFO-200"


def _is_no_data_or_raise(result: Dict[str, Any] | None) -> bool:
    """API RESULT 블록을 검사한다.

    서울 API는 인증키 오류 등도 HTTP 200으로 반환하므로, 상태코드만 믿으면
    오류가 "0건 수집 완료"로 위장된다. CODE 를 직접 확인해 명시적으로 실패시킨다.

    Returns:
        True  → INFO-200 (데이터 없음): 빈 결과로 정상 종료
        False → INFO-000 (정상) 또는 RESULT 없음: 계속 진행
    Raises:
        RuntimeError: 그 외 INFO-xxx / ERROR-xxx 오류 코드
    """
    if not result:
        return False
    code = str(result.get("CODE", ""))
    if code == _RESULT_OK:
        return False
    if code.startswith(_RESULT_NO_DATA):
        return True
    raise RuntimeError(f"API 오류 응답: {code} — {result.get('MESSAGE', '')}")


def paginate(
    service: str,
    limit: int | None = None,
    filters: List[str] | None = None,
) -> Iterator[List[Dict[str, Any]]]:
    """서울 열린데이터 광장 페이지네이션을 순회하며 배치(row 리스트)를 yield.

    Args:
        service: 서비스 식별자 (예: VwsmTrdarStorQq)
        limit: 최대 수집 행 수. None 또는 0 이면 전체.
        filters: 경로 끝에 붙는 요청 인자 값들(순서 중요). 예: ["20261"] → 분기 필터.
    """
    if not config.has_valid_api_key():
        raise RuntimeError("유효한 API 키가 없습니다. .env 의 SEOUL_API_KEY 를 확인하세요.")

    filter_path = "".join(f"{f}/" for f in (filters or []))
    collected = 0
    start = 1
    batch = config.BATCH_SIZE

    while True:
        if limit and collected >= limit:
            break

        end = start + batch - 1
        url = f"{config.API_BASE_URL}/{config.SEOUL_API_KEY}/json/{service}/{start}/{end}/{filter_path}"
        payload = fetch_json(url)

        block = payload.get(service)
        if block is None:
            # 서비스 블록이 없으면 최상위 RESULT 가 오류/데이터 없음을 알려준다.
            if _is_no_data_or_raise(payload.get("RESULT")):
                break  # 데이터 없음 → 빈 결과 정상 종료
            raise RuntimeError(f"예상하지 못한 API 응답 형식입니다 (서비스 블록 없음): {service}")

        # 서비스 블록 내부 RESULT 도 동일하게 검사 (페이지 범위 초과 등)
        if _is_no_data_or_raise(block.get("RESULT")):
            break

        rows = block.get("row")
        if not rows:
            break

        # limit 절단은 이곳에서만 책임진다 (호출부 중복 제거).
        if limit and collected + len(rows) > limit:
            rows = rows[: limit - collected]

        yield rows
        collected += len(rows)

        if len(rows) < batch:  # 마지막 페이지 (또는 limit 절단)
            break
        start += batch
