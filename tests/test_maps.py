import pandas as pd
import pydeck as pdk

from src import config
from src.maps import density_color, store_density_deck

COLS = config.COLS


def _map_df():
    return pd.DataFrame(
        {
            COLS.TRDAR_CD: ["1001", "1002", "1003"],
            COLS.TRDAR_CD_NM: ["A상권", "B상권", "C상권"],
            COLS.DISTRICT: ["중구", "강남구", "마포구"],
            COLS.LAT: [37.57, 37.50, 37.56],
            COLS.LON: [126.98, 127.03, 126.91],
            COLS.STORE_CO: [5, 30, 80],
        }
    )


def test_density_color_gradient():
    low = density_color(0, 0, 100)
    high = density_color(100, 0, 100)
    assert low[0] < high[0]  # 파랑 → 빨강: R 채널 증가
    assert len(low) == 4


def test_store_density_deck_uses_per_point_color():
    df = _map_df()
    deck = store_density_deck(df, title="테스트")
    assert isinstance(deck, pdk.Deck)
    assert len(deck.layers) == 1
    assert "color" in str(deck.layers[0].get_fill_color)
    colors = df[COLS.STORE_CO].apply(lambda v: density_color(v, 5, 80))
    assert colors.iloc[0] != colors.iloc[-1]
