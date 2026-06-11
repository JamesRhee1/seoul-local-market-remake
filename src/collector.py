"""서울 열린데이터 광장 API 데이터 수집기.

점포(Fact)와 상권 위치(Dimension) 데이터를 페이지네이션으로 수집해
data/raw 에 CSV 로 저장한다. 공통 수집 로직은 utils.paginate 가 담당한다.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from . import config
from .utils import get_logger, paginate

logger = get_logger(__name__)


_PROGRESS_LOG_EVERY = 10_000  # 진행 로그 간격 (행 수)


def _collect(
    service: str, limit: int | None, filters: List[str] | None = None
) -> List[Dict[str, Any]]:
    """주어진 서비스에서 행 목록을 수집한다.

    limit 절단은 paginate 가 책임지므로 여기서는 누적만 한다.
    """
    rows: List[Dict[str, Any]] = []
    last_logged = 0
    for batch in paginate(service, limit=limit, filters=filters):
        rows.extend(batch)
        # BATCH_SIZE 와 무관하게 1만 행마다 진행 상황을 남긴다.
        if len(rows) - last_logged >= _PROGRESS_LOG_EVERY:
            last_logged = len(rows)
            logger.info("%s: %d건 수집 중...", service, len(rows))
    logger.info("%s: 총 %d건 수집 완료", service, len(rows))
    return rows


def _save(rows: List[Dict[str, Any]], path: Path) -> Path | None:
    if not rows:
        logger.warning("수집된 데이터가 없어 저장을 건너뜁니다: %s", path.name)
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")
    logger.info("저장 완료: %s (%d행)", path, len(rows))
    return path


def collect_store_data(
    limit: int | None = None, quarter: str | None = None
) -> Path | None:
    """상권-점포 데이터를 수집해 data/raw 에 저장.

    Args:
        limit: 최대 수집 행 수. None 이면 설정값, 0 이면 전체.
        quarter: 기준 년분기 코드(예: 20261). None 이면 설정값(TARGET_QUARTER).
    """
    limit = config.COLLECT_LIMIT if limit is None else limit
    quarter = config.TARGET_QUARTER if quarter is None else quarter
    filters = [quarter] if quarter else None

    target = "전체" if not limit else f"{limit}행"
    scope = f"분기={quarter}" if quarter else "전체 분기"
    logger.info("점포 데이터 수집 시작 (목표: %s, %s)", target, scope)

    rows = _collect(config.SERVICE_STORE, limit or None, filters=filters)
    return _save(rows, config.RAW_STORE_FILE)


def collect_location_data() -> Path | None:
    """상권 위치(자치구 매핑) 메타데이터를 전체 수집해 data/raw 에 저장."""
    logger.info("위치 메타데이터 수집 시작")
    rows = _collect(config.SERVICE_LOCATION, limit=None)
    return _save(rows, config.RAW_LOCATION_FILE)


def main() -> None:
    if not config.has_valid_api_key():
        logger.error("유효한 API 키가 없습니다. .env 의 SEOUL_API_KEY 를 설정하세요.")
        return
    collect_store_data()
    collect_location_data()


if __name__ == "__main__":
    main()
