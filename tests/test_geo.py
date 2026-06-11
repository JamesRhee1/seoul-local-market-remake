from src.geo import seoul_tm_to_wgs84

# 강남역 상권 TM 좌표 (data/raw 위치 원천 기준)
_GANGNAM_TM_X = 202454
_GANGNAM_TM_Y = 444235
# WGS84 기대값: EPSG:5181 실증 + 공개 지도 기준 (±0.001° ≈ 100m)
_GANGNAM_LON = 127.0276
_GANGNAM_LAT = 37.4976


def test_seoul_tm_to_wgs84_gangnam_station():
    lon, lat = seoul_tm_to_wgs84(_GANGNAM_TM_X, _GANGNAM_TM_Y)
    assert abs(lon - _GANGNAM_LON) < 0.001
    assert abs(lat - _GANGNAM_LAT) < 0.001
