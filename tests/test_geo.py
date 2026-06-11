from src.geo import seoul_tm_to_wgs84


def test_seoul_tm_to_wgs84_known_point():
    lon, lat = seoul_tm_to_wgs84(197093, 453418)
    assert 126.9 < lon < 127.0
    assert 37.5 < lat < 37.7
