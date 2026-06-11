"""utils 의 HTTP 헬퍼(fetch_json/paginate) 동작 검증.

실제 네트워크 없이 requests-mock 으로 서울 API 응답을 흉내 낸다.
특히 "HTTP 200 인데 본문이 오류"인 서울 API 특성이 침묵 실패로
이어지지 않는지를 집중적으로 확인한다.
"""
from __future__ import annotations

import pytest
import requests

from src import config, utils

SERVICE = "TestSvc"
KEY = "TESTKEY1234"


@pytest.fixture(autouse=True)
def _fake_key(monkeypatch):
    """테스트 동안 유효한 키가 설정된 것처럼 동작시킨다."""
    monkeypatch.setattr(config, "SEOUL_API_KEY", KEY)
    monkeypatch.setattr(utils, "time", _NoSleepTime)


class _NoSleepTime:
    """재시도 백오프 대기를 제거해 테스트를 빠르게 유지한다."""

    @staticmethod
    def sleep(_seconds):
        return None


def _page_url(start: int, end: int) -> str:
    return f"{config.API_BASE_URL}/{KEY}/json/{SERVICE}/{start}/{end}/"


def _rows(n: int, offset: int = 0):
    return [{"ID": offset + i} for i in range(n)]


# ---------------------------------------------------------------------------
# fetch_json: 재시도/실패
# ---------------------------------------------------------------------------

def test_fetch_json_retries_then_succeeds(requests_mock):
    url = "http://example.test/data"
    requests_mock.get(
        url,
        [
            {"exc": requests.exceptions.ConnectTimeout},
            {"json": {"ok": True}, "status_code": 200},
        ],
    )
    assert utils.fetch_json(url) == {"ok": True}
    assert requests_mock.call_count == 2


def test_fetch_json_raises_after_all_retries(requests_mock):
    url = "http://example.test/always-fail"
    requests_mock.get(url, exc=requests.exceptions.ConnectTimeout)
    with pytest.raises(RuntimeError, match="모두 실패"):
        utils.fetch_json(url)
    assert requests_mock.call_count == config.MAX_RETRIES


# ---------------------------------------------------------------------------
# paginate: 오류 응답 명시적 실패 (침묵 실패 방지)
# ---------------------------------------------------------------------------

def test_paginate_raises_on_error_result(requests_mock):
    """인증키 오류 등은 HTTP 200 + RESULT 블록으로 와도 RuntimeError 여야 한다."""
    requests_mock.get(
        _page_url(1, config.BATCH_SIZE),
        json={"RESULT": {"CODE": "INFO-100", "MESSAGE": "인증키가 유효하지 않습니다."}},
    )
    with pytest.raises(RuntimeError, match="INFO-100"):
        list(utils.paginate(SERVICE))


def test_paginate_raises_on_error_inside_service_block(requests_mock):
    """서비스 블록 내부 RESULT 의 오류 코드도 동일하게 실패해야 한다."""
    requests_mock.get(
        _page_url(1, config.BATCH_SIZE),
        json={SERVICE: {"RESULT": {"CODE": "ERROR-500", "MESSAGE": "서버 오류"}}},
    )
    with pytest.raises(RuntimeError, match="ERROR-500"):
        list(utils.paginate(SERVICE))


def test_paginate_treats_no_data_as_empty(requests_mock):
    """INFO-200(데이터 없음)은 오류가 아니라 빈 결과로 정상 종료."""
    requests_mock.get(
        _page_url(1, config.BATCH_SIZE),
        json={"RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다."}},
    )
    assert list(utils.paginate(SERVICE)) == []


def test_paginate_raises_on_unexpected_payload(requests_mock):
    """서비스 블록도 RESULT 도 없는 응답은 형식 오류로 실패해야 한다."""
    requests_mock.get(_page_url(1, config.BATCH_SIZE), json={"unexpected": 1})
    with pytest.raises(RuntimeError, match="응답 형식"):
        list(utils.paginate(SERVICE))


# ---------------------------------------------------------------------------
# paginate: 페이지 종료 조건
# ---------------------------------------------------------------------------

def test_paginate_stops_on_short_last_page(requests_mock):
    """마지막 페이지(행 수 < BATCH_SIZE)에서 추가 요청 없이 종료한다."""
    batch = config.BATCH_SIZE
    requests_mock.get(
        _page_url(1, batch),
        json={SERVICE: {"row": _rows(batch)}},
    )
    requests_mock.get(
        _page_url(batch + 1, batch * 2),
        json={SERVICE: {"row": _rows(3, offset=batch)}},
    )
    batches = list(utils.paginate(SERVICE))
    assert [len(b) for b in batches] == [batch, 3]
    assert requests_mock.call_count == 2


def test_paginate_trims_to_limit(requests_mock):
    """limit 절단은 paginate 단독 책임 — 총 행 수가 limit 을 넘지 않아야 한다."""
    batch = config.BATCH_SIZE
    requests_mock.get(
        _page_url(1, batch),
        json={SERVICE: {"row": _rows(batch)}},
    )
    limit = batch - 7  # 한 페이지보다 작은 limit
    batches = list(utils.paginate(SERVICE, limit=limit))
    assert sum(len(b) for b in batches) == limit
    assert requests_mock.call_count == 1  # 추가 페이지 요청 없음


def test_paginate_requires_api_key(monkeypatch):
    monkeypatch.setattr(config, "SEOUL_API_KEY", "")
    with pytest.raises(RuntimeError, match="API 키"):
        list(utils.paginate(SERVICE))


def test_read_str_setting_tolerates_missing_streamlit_secrets(monkeypatch):
    """CI 처럼 secrets.toml 이 없을 때도 설정 읽기가 실패하지 않아야 한다."""
    monkeypatch.delenv("SEOUL_API_KEY", raising=False)

    class BrokenSecrets:
        def __contains__(self, key):
            raise FileNotFoundError("No secrets found")

    monkeypatch.setattr(config, "_get_streamlit_secrets", lambda: BrokenSecrets())
    assert config._read_str_setting("SEOUL_API_KEY", "fallback") == "fallback"
