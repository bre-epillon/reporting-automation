import streamlit as st
from datetime import datetime
import pandas as pd
import os
from shared.colored_logging import info, warning, error, debug, success


def initialize_session_state(debug: bool = False):
    """Initialize or retrieve the session state with repositories and services."""

    # Get current date information
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")
    month = now.strftime("%B")
    quarter = (now.month - 1) // 3 + 1
    year = now.year
    uwy = year - 1 if month in ["January", "February", "March"] else year

    st.session_state.setdefault("current_date", current_date)
    st.session_state.setdefault("time", time)
    st.session_state.setdefault("month", month)
    st.session_state.setdefault("quarter", quarter)
    st.session_state.setdefault("year", year)
    st.session_state.setdefault("uwy", uwy)

    # import data if not already in session state and cache them in session state
    if st.session_state.initalized == False:
        st.session_state.initalized = True
