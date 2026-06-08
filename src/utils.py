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
            wait = config.RETRY_BACKOFF * attempt
            logger.warning(
                "요청 실패(%s/%s): %s | %s초 후 재시도",
                attempt, config.MAX_RETRIES, _mask_key(url), wait,
            )
            time.sleep(wait)
    raise RuntimeError(f"API 요청이 {config.MAX_RETRIES}회 모두 실패했습니다: {last_exc}")


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
        if not block or not block.get("row"):
            break

        rows = block["row"]
        yield rows
        collected += len(rows)

        if len(rows) < batch:  # 마지막 페이지
            break
        start += batch
