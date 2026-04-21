import streamlit as st
import plotly.express as px
from presentation.state.session_state_manager import initialize_session_state
import pandas as pd
from shared.constants import LOB_MAPPING
from shared.colored_logging import info, warning, error, debug, success
from services.premiums_visualizer import PremiumsVisualizer
from shared.data_api import fetch_data

st.set_page_config(page_title="Report Generator", page_icon="📈", layout="wide")

initialize_session_state()
# get_sidebar()

historical_premiums = fetch_data()

with st.expander("Show Raw Data"):
    st.write("### Data Preview")
    st.dataframe(historical_premiums)

    st.write("### Basic Stats")
    st.write(historical_premiums.describe())

    current_uwy = st.session_state.uwy

st.title("Premiums Analyzer")

st.write("## Premiums Over Time (By Year)")

macro_lob = st.segmented_control(
    options=list(LOB_MAPPING.keys()),
    key="selected_lob",
    help="Select LoB to view.",
    label="LoB to Display",
    default="Energy",
)

display_mode = st.segmented_control(
    options=["standard", "cumulative"],
    key="selected_display_mode",
    help="Select how to view the premiums written.",
    label="View",
    default="standard",
)

pv = PremiumsVisualizer(historical_premiums)

new_fig = pv.get_figure(
    macro_lob=macro_lob,
    color_map_style="focus",
    display_mode=display_mode,
    current_uwy=current_uwy,
)
st.plotly_chart(new_fig, width="stretch")
