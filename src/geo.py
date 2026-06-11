"""좌표 변환 (순수 함수)."""
from __future__ import annotations

from pyproj import Transformer

# 서울 열린데이터 상권영역(TbgisTrdarRelm) TM 좌표: GRS80 중부원점(EPSG:5181).
# EPSG:5174 는 Korean 1985(Bessel) 기반이라 GRS80 명칭과 불일치한다.
# 실증: 강남역 상권(XCNTS=202454, YDNTS=444235)을 5181로 변환하면
# (127.0278°, 37.4976°)로 실제 강남역(≈127.0276°, 37.4979°)에 근접하고,
# 5174 변환은 lat≈37.500으로 약 313m 북쪽으로 치우친다.
_TM_TO_WGS84 = Transformer.from_crs(5181, 4326, always_xy=True)


def seoul_tm_to_wgs84(x: float, y: float) -> tuple[float, float]:
    """TM 좌표를 WGS84 경위도로 변환한다."""
    lon, lat = _TM_TO_WGS84.transform(float(x), float(y))
    return lon, lat
