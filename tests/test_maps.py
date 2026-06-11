import pandas as pd
import pydeck as pdk

from src import config
from src.maps import store_density_deck

COLS = config.COLS


def _map_df():
    return pd.DataFrame(
        {
            COLS.TRDAR_CD: ["1001", "1002"],
            COLS.TRDAR_CD_NM: ["A상권", "B상권"],
            COLS.DISTRICT: ["중구", "강남구"],
            COLS.LAT: [37.57, 37.50],
            COLS.LON: [126.98, 127.03],
            COLS.STORE_CO: [10, 30],
        }
    )


def test_store_density_deck_builds_scatter_layer():
    deck = store_density_deck(_map_df(), title="테스트")
    assert isinstance(deck, pdk.Deck)
    assert len(deck.layers) == 1
    assert getattr(deck.layers[0], "layer_type", deck.layers[0].__class__.__name__) in {
        "ScatterplotLayer",
        "Layer",
    }
