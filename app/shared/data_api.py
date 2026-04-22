from pathlib import Path

import pandas as pd
import streamlit as st

from shared.colored_logging import error, info

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PREMIUMS_DATA_PATH = PROJECT_ROOT / "inputs" / "premiums_2026-04-22.csv"


@st.cache_data(show_spinner=True)
def fetch_data() -> pd.DataFrame:
    info("Fetching data...")
    try:
        return pd.read_csv(PREMIUMS_DATA_PATH)
    except Exception as exc:
        error(f"Error fetching data: {exc}")
        return pd.DataFrame()
