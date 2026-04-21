import streamlit as st
from presentation.state.session_state_manager import initialize_session_state
from shared.colored_logging import info, warning, error, debug, success
import pandas as pd
from shared.data_api import fetch_data


def main():
    initialize_session_state()

    st.title("Hello, there!")
    st.write("write here some documentation")

    historical_premiums = fetch_data()

    st.write("### Data Preview")
    st.dataframe(historical_premiums)

    st.write("### Basic Stats")
    st.write(historical_premiums.describe())


# Function to fetch data from our FastAPI backend
if __name__ == "__main__":
    main()
