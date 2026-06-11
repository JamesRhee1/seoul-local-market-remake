"""좌표 변환 (순수 함수)."""
from __future__ import annotations

from pyproj import Transformer

# 서울 열린데이터 상권 좌표계: GRS80 중부원점(EPSG:5174)
_TM_TO_WGS84 = Transformer.from_crs(5174, 4326, always_xy=True)


def seoul_tm_to_wgs84(x: float, y: float) -> tuple[float, float]:
    """TM 좌표를 WGS84 경위도로 변환한다."""
    lon, lat = _TM_TO_WGS84.transform(float(x), float(y))
    return lon, lat
