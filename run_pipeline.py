"""데이터 파이프라인 오케스트레이터.

수집 → 전처리 → README 리포트를 순서대로 실행한다.
각 단계는 독립 모듈(collector/preprocessor/report)이며, 이 파일이
단계 간 순서와 실패 정책을 한곳에서 관리한다.

사용법:
    python run_pipeline.py
"""
from __future__ import annotations

from src import collector, config, preprocessor, report
from src.utils import get_logger

logger = get_logger(__name__)


def main() -> None:
    quarters = config.get_target_quarters()
    if config.has_valid_api_key() and not quarters:
        logger.warning(
            "TARGET_QUARTER 가 비어 있어 2025년 4분기(%s)를 사용합니다.",
            ", ".join(config.DEMO_QUARTERS),
        )
        quarters = config.DEMO_QUARTERS

    # 1) 수집 — API 키가 있을 때만. 없으면 기존 raw/샘플 데이터로 다음 단계 진행.
    if config.has_valid_api_key():
        logger.info("[1/3] 데이터 수집 시작 (%d개 분기)", len(quarters))
        for i, quarter in enumerate(quarters, start=1):
            logger.info("--- 분기 %s (%d/%d) ---", quarter, i, len(quarters))
            collector.collect_store_data(quarter=quarter)
            if i == 1:
                collector.collect_location_data()
            logger.info("[2/3] 전처리 시작 (분기 %s)", quarter)
            if preprocessor.run() is None:
                logger.info("전처리 결과가 없습니다. 대시보드는 data/sample/ 폴백으로 동작합니다.")
    else:
        logger.info("[1/3] API 키가 없어 수집을 건너뜁니다 (.env 의 SEOUL_API_KEY). "
                    "기존 raw 데이터 또는 샘플로 진행합니다.")
        logger.info("[2/3] 전처리 시작")
        if preprocessor.run() is None:
            logger.info("전처리 결과가 없습니다. 대시보드는 data/sample/ 폴백으로 동작합니다.")

    # 3) README 인사이트 — 실패해도 파이프라인 전체는 성공으로 둔다 (문서 갱신은 부수 작업).
    logger.info("[3/3] README 인사이트 갱신")
    try:
        report.update_readme()
    except Exception as exc:  # noqa: BLE001
        logger.warning("README 자동 갱신 실패(무시): %s", exc)

    logger.info("파이프라인 완료")


if __name__ == "__main__":
    main()
