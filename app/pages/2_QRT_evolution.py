import streamlit as st
import pandas as pd
from jinja2 import Template
import io

from presentation.state.session_state_manager import initialize_session_state

st.set_page_config(page_title="Report Generator", page_icon="📈", layout="wide")
initialize_session_state()

# --- 3. STREAMLIT APP ---
st.set_page_config(page_title="QRT Evolution Reporter", layout="wide")
st.title("📊 QRT (Solvency II) Quarterly Evolution")


# --- 1. LATEX JINJA TEMPLATE ---
# This template uses pdflscape for landscape orientation and longtable for multipage support
LATEX_TEMPLATE = """
\\begin{landscape}
\\section{QRT Quarterly Evolution}

\\begin{longtable}{ l {% for col in columns[1:] %} r {% endfor %} }
\\caption{Quarterly Evolution of Solvency II Modules} \\label{tab:qrt_evolution} \\\\
\\toprule
{% for col in columns %}\\textbf{ {{ col }} }{% if not loop.last %} & {% endif %}{% endfor %} \\\\
\\midrule
\\endfirsthead

\\multicolumn{ {{ columns|length }} }{c}
{{\\bfseries \\tablename\\ \\thetable{} -- continued from previous page}} \\\\
\\toprule
{% for col in columns %}\\textbf{ {{ col }} }{% if not loop.last %} & {% endif %}{% endfor %} \\\\
\\midrule
\\endhead

\\midrule
\\multicolumn{ {{ columns|length }} }{r}{{Continued on next page}} \\\\
\\endfoot

\\bottomrule
\\endlastfoot

{% for row in rows %}
    {% for cell in row %}{{ cell }}{% if not loop.last %} & {% endif %}{% endfor %} \\\\
{% endfor %}
\\end{longtable}
\\end{landscape}
"""


# --- 2. HELPER FUNCTIONS ---
def clean_and_parse_data(file):

    df = pd.read_excel(
        file,
        sheet_name="Table",
        usecols="B:L",
        skiprows=1,
        nrows=26,
        engine="openpyxl",
    )

    # Drop completely empty columns/rows if any exist on the edges
    df.dropna(how="all", axis=1, inplace=True)
    df.dropna(how="all", axis=0, inplace=True)

    # Rename the first column for clarity
    df.rename(columns={df.columns[0]: "Module / Submodule"}, inplace=True)

    # Replace '-' with 0
    df.replace("-", 0, inplace=True)
    df.fillna(0, inplace=True)

    return df


def escape_latex_chars(val):
    """Escapes special LaTeX characters like & and %"""
    if isinstance(val, str):
        return val.replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")
    return val


def format_for_latex(df):
    """Formats numbers with commas and escapes strings for LaTeX."""
    df_latex = df.copy()
    for col in df_latex.columns:
        if df_latex[col].dtype in ["float64", "int64"]:
            # Format numbers to string with thousand separators, no decimals
            df_latex[col] = df_latex[col].apply(
                lambda x: f"{x:,.0f}" if x != 0 else "-"
            )
        else:
            # Escape strings (e.g., changing "P&R" to "P\&R")
            df_latex[col] = df_latex[col].apply(escape_latex_chars)

    # Also escape column names just in case
    escaped_columns = [escape_latex_chars(col) for col in df_latex.columns]

    return df_latex, escaped_columns


uploaded_file = st.file_uploader("Upload your QRT Excel file", type=["xlsx", "xls"])

if uploaded_file is not None:
    # --- Parse Data ---
    with st.spinner("Parsing data..."):
        df = clean_and_parse_data(uploaded_file)

    # --- Summarize in Streamlit ---
    st.subheader("Data Overview")

    # Optional: Format the dataframe nicely for the Streamlit UI
    st.dataframe(
        df.style.format(
            formatter={
                col: "{:,.0f}"
                for col in df.columns
                if df[col].dtype in ["float64", "int64"]
            }
        ),
        width="stretch",
        hide_index=True,
    )

    # --- Generate LaTeX ---
    st.subheader("Generate LaTeX Document Section")

    if st.button("Generate LaTeX Code"):
        with st.spinner("Generating LaTeX template..."):
            # Format data specifically for LaTeX (comma separated strings, escaped characters)
            df_latex, escaped_columns = format_for_latex(df)

            # Prepare data for Jinja
            rows_data = df_latex.values.tolist()

            # Render Jinja template
            jinja_template = Template(LATEX_TEMPLATE)
            latex_code = jinja_template.render(columns=escaped_columns, rows=rows_data)

            st.success("LaTeX code generated successfully!")

            # Display inside a code block so it can be easily copied
            st.code(latex_code, language="latex")

            # Provide a download button for the .tex file
            st.download_button(
                label="Download .tex file",
                data=latex_code,
                file_name="qrt_evolution.tex",
                mime="text/plain",
            )

else:
    st.info("Please upload an Excel file to get started.")
