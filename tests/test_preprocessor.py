import pandas as pd

from src import config
from src.preprocessor import build_dimension, clean_numeric, merge_market_data

COLS = config.COLS


def _store_df():
    return pd.DataFrame(
        {
            COLS.TRDAR_CD: [1001, 1002, 9999],
            COLS.INDUSTRY: ["커피-음료", "한식음식점", "커피-음료"],
            COLS.STORE_CO: ["10", "5", None],   # 문자열/결측 혼재
            COLS.OPEN_CO: [2, 1, 0],
            COLS.CLOSE_CO: [1, 0, 0],
        }
    )


def _location_df():
    return pd.DataFrame(
        {
            COLS.TRDAR_CD: [1001, 1001, 1002],  # 중복 포함
            COLS.DISTRICT: ["중구", "중구", "강남구"],
        }
    )


def test_clean_numeric_coerces_and_fills():
    df = clean_numeric(_store_df())
    assert df[COLS.STORE_CO].tolist() == [10.0, 5.0, 0.0]
    assert pd.api.types.is_numeric_dtype(df[COLS.STORE_CO])


def test_build_dimension_dedupes():
    dim = build_dimension(_location_df())
    assert len(dim) == 2
    # dtype 구현(object vs StringDtype)은 pandas 버전에 따라 달라지므로
    # "문자열 키"라는 동작 자체를 검증한다 (pandas 2/3 호환).
    assert pd.api.types.is_string_dtype(dim[COLS.TRDAR_CD])
    assert dim[COLS.TRDAR_CD].tolist() == ["1001", "1002"]


def test_merge_attaches_district_and_handles_unknown():
    merged = merge_market_data(_store_df(), _location_df())
    assert len(merged) == 3
    # 매칭된 자치구
    row = merged[merged[COLS.TRDAR_CD] == "1001"].iloc[0]
    assert row[COLS.DISTRICT] == "중구"
    # 매칭 실패(9999) → Unknown
    assert (merged[COLS.DISTRICT] == "Unknown").sum() == 1
    # 수치형 정제 적용
    assert pd.api.types.is_numeric_dtype(merged[COLS.STORE_CO])
