from pathlib import Path

import streamlit as st

from presentation.state.session_state_manager import initialize_session_state
from services.premiums_visualizer import PremiumsVisualizer
from shared.colored_logging import debug
from shared.constants import LOB_MAPPING
from shared.data_api import fetch_data
from shared.reporting_utils import compile_latex_to_pdf

st.set_page_config(page_title="Premiums Analyzer", layout="wide")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
IMG_DIR = PROJECT_ROOT / "images"
TEX_FILENAME = PROJECT_ROOT / "main_small.tex"

initialize_session_state()
current_uwy = st.session_state.get("uwy", 2026)

historical_premiums = fetch_data()

with st.expander("Show Raw Data"):
    st.write("### Data Preview")
    st.dataframe(historical_premiums)

    st.write("### Basic Stats")
    st.write(historical_premiums.describe())

premium_visualizer = PremiumsVisualizer(historical_premiums)

st.title("Premiums Analyzer")

st.write("## Premiums Over Time (By Year)")

if st.button("Generate Report", type="primary"):
    with st.spinner("Generating report... This might take a minute."):
        IMG_DIR.mkdir(parents=True, exist_ok=True)

        st.info("Generating visuals...")
        export_engines = set()
        for lob in list(LOB_MAPPING.keys()):
            debug(f"Processing the generation of images for LoB: {lob}")
            image_path = IMG_DIR / f"{lob}_premium.png"
            debug(f"Saving image to: {image_path}")
            export_engine = premium_visualizer.write_image(
                macro_lob=lob,
                output_path=image_path,
                current_uwy=current_uwy,
                engine="pillow",
            )
            export_engines.add(export_engine)
            debug(f"Image saved to: {image_path}")

        st.info("Compiling PDF...")
        if "pillow" in export_engines:
            st.caption(
                "Report visuals were rendered with the built-in PNG exporter "
                "because Plotly/Kaleido static image export is unavailable in this environment."
            )

        pdf_path = compile_latex_to_pdf(TEX_FILENAME, output_stem="final_report")
        if pdf_path:
            st.success("Report generated successfully!")

            with open(pdf_path, "rb") as pdf_file:
                st.download_button(
                    label="Download PDF Report",
                    data=pdf_file,
                    file_name="Automated_Premium_Report.pdf",
                    mime="application/pdf",
                )
