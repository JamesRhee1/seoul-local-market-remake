import pandas as pd
import pytest

from src import config
from src.preprocessor import (
    build_dimension,
    clean_numeric,
    merge_market_data,
    split_by_quarter,
    validate_schema,
)

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
            COLS.TRDAR_CD_NM: ["위치상권A", "위치상권A", "위치상권B"],
            COLS.TM_X: [197093, 197093, 198000],
            COLS.TM_Y: [453418, 453418, 454000],
        }
    )


def _store_df_with_trdar_name():
    return pd.DataFrame(
        {
            COLS.TRDAR_CD: [1001, 1002],
            COLS.TRDAR_CD_NM: ["점포상권A", "점포상권B"],
            COLS.INDUSTRY: ["커피-음료", "한식음식점"],
            COLS.STORE_CO: [10, 5],
            COLS.OPEN_CO: [2, 1],
            COLS.CLOSE_CO: [1, 0],
        }
    )


def test_clean_numeric_coerces_and_fills():
    df = clean_numeric(_store_df())
    assert df[COLS.STORE_CO].tolist() == [10.0, 5.0, 0.0]
    assert pd.api.types.is_numeric_dtype(df[COLS.STORE_CO])


def test_build_dimension_dedupes():
    dim = build_dimension(_location_df())
    assert len(dim) == 2
    assert COLS.LON in dim.columns
    assert COLS.LAT in dim.columns
    # dtype 구현(object vs StringDtype)은 pandas 버전에 따라 달라지므로
    # "문자열 키"라는 동작 자체를 검증한다 (pandas 2/3 호환).
    assert pd.api.types.is_string_dtype(dim[COLS.TRDAR_CD])
    assert dim[COLS.TRDAR_CD].tolist() == ["1001", "1002"]


def test_validate_schema_passes_on_required_cols():
    validate_schema(_store_df(), config.REQUIRED_STORE_COLS, "store")
    validate_schema(_location_df(), config.REQUIRED_LOCATION_COLS, "location")


def test_validate_schema_raises_with_missing_cols():
    df = _store_df().drop(columns=[COLS.STORE_CO, COLS.OPEN_CO])
    with pytest.raises(ValueError) as exc:
        validate_schema(df, config.REQUIRED_STORE_COLS, "store")
    # 누락된 컬럼명이 에러 메시지에 모두 나타나야 디버깅이 쉽다
    assert COLS.STORE_CO in str(exc.value)
    assert COLS.OPEN_CO in str(exc.value)


def test_split_by_quarter_groups_rows():
    df = pd.DataFrame(
        {
            COLS.QUARTER: [20253, 20253, 20254],
            COLS.TRDAR_CD: [1, 2, 3],
        }
    )
    parts = split_by_quarter(df)
    assert set(parts) == {"20253", "20254"}
    assert len(parts["20253"]) == 2
    assert len(parts["20254"]) == 1


def test_merge_preserves_trdar_name_without_suffix_columns():
    """점포·위치 양쪽에 TRDAR_CD_NM 이 있어도 Fact 값이 유지되어야 한다."""
    merged = merge_market_data(_store_df_with_trdar_name(), _location_df())
    assert COLS.TRDAR_CD_NM in merged.columns
    assert not any(str(c).endswith("_x") or str(c).endswith("_y") for c in merged.columns)
    assert merged[COLS.TRDAR_CD_NM].tolist() == ["점포상권A", "점포상권B"]


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
