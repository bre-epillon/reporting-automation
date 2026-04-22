import pandas as pd
import streamlit as st
from jinja2 import Template
from pathlib import Path

from presentation.state.session_state_manager import initialize_session_state

initialize_session_state()

st.set_page_config(page_title="QRT Evolution Reporter", layout="wide")
st.title("QRT (Solvency II) Quarterly Evolution")


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
{\\bfseries \\tablename\\ \\thetable{} -- continued from previous page} \\\\
\\toprule
{% for col in columns %}\\textbf{ {{ col }} }{% if not loop.last %} & {% endif %}{% endfor %} \\\\
\\midrule
\\endhead

\\midrule
\\multicolumn{ {{ columns|length }} }{r}{Continued on next page} \\\\
\\endfoot

\\bottomrule
\\endlastfoot

{% for row in rows %}
    {% for cell in row %}{{ cell }}{% if not loop.last %} & {% endif %}{% endfor %} \\\\
{% endfor %}
\\end{longtable}
\\end{landscape}
"""


def clean_and_parse_data(file):
    df = pd.read_excel(
        file,
        sheet_name="Table",
        usecols="B:L",
        skiprows=1,
        nrows=26,
        engine="openpyxl",
    )

    df.dropna(how="all", axis=1, inplace=True)
    df.dropna(how="all", axis=0, inplace=True)
    df.rename(columns={df.columns[0]: "Module / Submodule"}, inplace=True)
    df.rename(columns={"Counterparty Default Module": "CDF Module"}, inplace=True)
    df.replace("-", 0, inplace=True)
    df.fillna(0, inplace=True)

    return df


def escape_latex_chars(val):
    """Escape a few common LaTeX-sensitive characters in text cells."""
    if isinstance(val, str):
        return val.replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")
    return val


def format_for_latex(df):
    """Format numbers and escape text before injecting the table into LaTeX."""
    df_latex = df.copy()
    for col in df_latex.columns:
        if df_latex[col].dtype in ["float64", "int64"]:
            df_latex[col] = df_latex[col].apply(
                lambda x: f"{x:,.0f}" if x != 0 else "-"
            )
        else:
            df_latex[col] = df_latex[col].apply(escape_latex_chars)

    escaped_columns = [escape_latex_chars(col) for col in df_latex.columns]

    return df_latex, escaped_columns


def export_latex_to_file(latex_code):
    """Saves the generated LaTeX code to src/qrt_evolution.tex relative to project root."""
    project_root = Path(__file__).resolve().parents[2]
    output_path = project_root / "src" / "qrt_evolution.tex"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(latex_code)


uploaded_file = st.file_uploader("Upload your QRT Excel file", type=["xlsx", "xls"])

if uploaded_file is not None:
    with st.spinner("Parsing data..."):
        df = clean_and_parse_data(uploaded_file)

    st.subheader("Data Overview")
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

    st.subheader("Generate LaTeX Document Section")

    if st.button("Generate LaTeX Code"):
        with st.spinner("Generating LaTeX template..."):
            df_latex, escaped_columns = format_for_latex(df)
            rows_data = df_latex.values.tolist()

            jinja_template = Template(LATEX_TEMPLATE)
            latex_code = jinja_template.render(columns=escaped_columns, rows=rows_data)

            export_latex_to_file(latex_code)
            st.success("LaTeX code generated successfully!")
            st.code(latex_code, language="latex")
            st.download_button(
                label="Download .tex file",
                data=latex_code,
                file_name="qrt_evolution.tex",
                mime="text/plain",
            )
else:
    st.info("Please upload an Excel file to get started.")
