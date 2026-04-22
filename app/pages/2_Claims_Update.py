import re
from pathlib import Path

import pandas as pd
import streamlit as st
from jinja2 import Template

from presentation.state.session_state_manager import initialize_session_state
from shared.constants import LOB_MAPPING

initialize_session_state()

st.set_page_config(page_title="Claims Updates", layout="wide")
st.title("Claims Quarterly Updates")

SOURCE_SHEET_NAME = "4) Pot. Large Losses wo Reserve"

# The workbook contains claim references like CFIL19XJO0167 and compact variants
# such as CFIL23XKE0071/2, so the country segment after X is treated as optional
# and slash-suffixed sequences are expanded.
CLAIM_ID_PATTERN = re.compile(r"(C[A-Z]{3}\d{2}X(?:[A-Z]{2})?)(\d{4})(?:/(\d{1,4}))?")

CLAIM_PREFIX_TO_SUBLOB = {
    "BON": "DCBON",
    "CAR": "DCLIA",
    "ENR": "Energy",
    "FIL": "DCFIL",
    "FRO": "DCFRO",
    "LIA": "DCLIA",
    "MAR": "DCMAR",
    "MOT": "DCLIA",
    "PRO": "PRTOT",
    "SPE": "DCSPE",
}

TEXT_HINT_TO_SUBLOB = (
    ("ENERGY OFFSHORE", "ENOFF"),
    ("ENERGY ONSHORE", "ENONS"),
    ("ENERGY", "Energy"),
    ("CONSTRUCTION", "DCPRO"),
    ("BONDS", "DCBON"),
    ("MOTOR", "DCLIA"),
)

DIRECT_LOB_LABELS = set(LOB_MAPPING)

# LATEX_TEMPLATE = """
# \\begin{longtable}{ {% for _ in columns %} l {% endfor %} }
# \\caption{Potential Large Losses Without Reserve for {{ lob }}} \\label{tab:potential-large-losses-without-reserve-{{ lob }}} \\\\
# \\toprule
# \\toprule
# {% for col in columns %}\\textbf{ {{ col }} }{% if not loop.last %} & {% endif %}{% endfor %} \\\\
# \\midrule
# \\endfirsthead

# \\toprule
# {% for col in columns %}\\textbf{ {{ col }} }{% if not loop.last %} & {% endif %}{% endfor %} \\\\
# \\midrule
# \\endhead

# {% for row in rows %}
# {% for cell in row %}{{ cell }}{% if not loop.last %} & {% endif %}{% endfor %} \\\\
# {% endfor %}

# \\bottomrule
# \\end{longtable}
# """
LATEX_TEMPLATE = """
\\subsection*{Potential Large Losses Without Reserve for {{ lob }}}

\\begin{itemize}
{% for row in rows %}
  \\item ({{ row['Sub-LoB'] }}, {{ row['UWY'] }}) \\textbf{ {{ row['Loss Name'] }} }: ``{{ row['Claims Judgement'] }}'' ({{ row['Exposure'] }})
{% endfor %}
\\end{itemize}
"""


def normalize_column_name(column_name) -> str:
    """Trim whitespace/newlines while keeping the original business labels readable."""
    if pd.isna(column_name):
        return ""
    return " ".join(str(column_name).split())


def escape_latex_chars(value):
    if isinstance(value, str):
        return (
            value.replace("\\", r"\textbackslash{}")
            .replace("&", r"\&")
            .replace("%", r"\%")
            .replace("_", r"\_")
            .replace("$", r"\$")
        )
    return value


def format_for_latex(df: pd.DataFrame, lob=None) -> tuple[pd.DataFrame, list[str]]:
    df_latex = df[df.LoB == lob].copy()
    columns_to_print = ["Sub-LoB", "UWY", "Loss Name", "Claims Judgement", "Exposure"]
    df_latex = df_latex[columns_to_print]

    for col in df_latex.columns:
        if pd.api.types.is_numeric_dtype(df_latex[col]):
            df_latex[col] = df_latex[col].apply(
                lambda value: f"{value:,.0f}" if pd.notna(value) else ""
            )
        else:
            df_latex[col] = df_latex[col].apply(
                lambda value: escape_latex_chars(value) if pd.notna(value) else ""
            )

    escaped_columns = [escape_latex_chars(column) for column in df_latex.columns]
    return df_latex, escaped_columns


def export_latex_to_file(latex_code: str, lob: str = "Energy") -> Path:
    project_root = Path(__file__).resolve().parents[2]
    output_path = project_root / "src" / f"potential_large_losses_{lob}.tex"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(latex_code, encoding="utf-8")
    return output_path


def expand_claim_id_match(match: re.Match) -> list[str]:
    """Expand compact claim references like CFIL23XKE0071/2 into both claim ids."""
    stem, first_suffix, second_suffix = match.groups()
    claim_ids = [f"{stem}{first_suffix}"]

    if second_suffix:
        if len(second_suffix) < len(first_suffix):
            expanded_suffix = (
                first_suffix[: len(first_suffix) - len(second_suffix)] + second_suffix
            )
        else:
            expanded_suffix = second_suffix
        claim_ids.append(f"{stem}{expanded_suffix}")

    return claim_ids


def extract_claim_ids(*values) -> list[str]:
    extracted_ids = []
    seen_ids = set()

    for value in values:
        if pd.isna(value):
            continue

        normalized_value = str(value).upper()
        for match in CLAIM_ID_PATTERN.finditer(normalized_value):
            for claim_id in expand_claim_id_match(match):
                if claim_id not in seen_ids:
                    seen_ids.add(claim_id)
                    extracted_ids.append(claim_id)

    return extracted_ids


def guess_lob_details(
    raw_claim_text: str, lob_claim_ref_text: str, claim_ids: list[str]
) -> tuple[str, str]:
    joined_text_parts = []
    for part in (raw_claim_text, lob_claim_ref_text):
        if pd.notna(part):
            joined_text_parts.append(str(part).upper())
    joined_text = " ".join(joined_text_parts)

    guessed_sublob = None
    for text_hint, sublob in TEXT_HINT_TO_SUBLOB:
        if text_hint in joined_text:
            guessed_sublob = sublob
            break

    if guessed_sublob is None and claim_ids:
        claim_prefix = claim_ids[0][1:4]
        guessed_sublob = CLAIM_PREFIX_TO_SUBLOB.get(claim_prefix)

    if guessed_sublob in DIRECT_LOB_LABELS:
        guessed_lob = guessed_sublob
    else:
        guessed_lob = "Unknown"
        for lob_name, sublobs in LOB_MAPPING.items():
            if guessed_sublob in sublobs:
                guessed_lob = lob_name
                break

    return guessed_lob, guessed_sublob or "Unknown"


def clean_and_parse_data(file) -> pd.DataFrame:
    df = pd.read_excel(
        file,
        sheet_name=SOURCE_SHEET_NAME,
        skiprows=2,
        engine="openpyxl",
    )

    df.columns = [normalize_column_name(column) for column in df.columns]
    df.dropna(how="all", axis=1, inplace=True)
    df.dropna(how="all", axis=0, inplace=True)

    rename_map = {}
    unnamed_columns = [column for column in df.columns if column.startswith("Unnamed:")]
    if unnamed_columns:
        rename_map[unnamed_columns[0]] = "Claim Ref (raw)"
    if len(unnamed_columns) > 1:
        rename_map[unnamed_columns[-1]] = "Additional Notes"
    df.rename(columns=rename_map, inplace=True)

    if "LOB / Claim Ref" not in df.columns:
        raise ValueError(
            f"Could not find the expected 'LOB / Claim Ref' column in sheet '{SOURCE_SHEET_NAME}'."
        )

    if "Claim Ref (raw)" not in df.columns:
        df.insert(0, "Claim Ref (raw)", pd.NA)

    df = df[
        df[["Claim Ref (raw)", "LOB / Claim Ref", "Loss Name"]].notna().any(axis=1)
    ].copy()

    for column in df.select_dtypes(include=["object", "str"]).columns:
        df[column] = df[column].map(
            lambda value: " ".join(str(value).split()) if pd.notna(value) else value
        )

    df["Claim IDs"] = df.apply(
        lambda row: extract_claim_ids(row["Claim Ref (raw)"], row["LOB / Claim Ref"]),
        axis=1,
    )
    df["Primary Claim ID"] = df["Claim IDs"].apply(
        lambda claim_ids: claim_ids[0] if claim_ids else pd.NA
    )
    df[["Guessed LoB", "Guessed Sub-LoB"]] = df.apply(
        lambda row: pd.Series(
            guess_lob_details(
                raw_claim_text=row["Claim Ref (raw)"],
                lob_claim_ref_text=row["LOB / Claim Ref"],
                claim_ids=row["Claim IDs"],
            )
        ),
        axis=1,
    )
    df["Claim IDs"] = df["Claim IDs"].apply(lambda claim_ids: ", ".join(claim_ids))

    # ordered_columns = [
    #     "Guessed LoB",
    #     "Guessed Sub-LoB",
    #     "Primary Claim ID",
    #     "Claim IDs",
    #     "Claim Ref (raw)",
    #     "LOB / Claim Ref",
    # ]
    # remaining_columns = [
    #     column for column in df.columns if column not in ordered_columns
    # ]
    columns_to_keep = [
        "LoB",
        "Sub-LoB",
        "Primary Claim ID",
        "UWY",
        "Loss Name",
        "Claims Judgement",
        "Exposure",
    ]
    rename_map = {
        "Guessed LoB": "LoB",
        "Guessed Sub-LoB": "Sub-LoB",
        "Claims’ judgement on the likelihood to materialise": "Claims Judgement",
        "Our Maximum Exposure": "Exposure",
    }
    df.rename(columns=rename_map, inplace=True)
    return df[columns_to_keep]


uploaded_file = st.file_uploader(
    "Upload your Claims updates file", type=["xlsx", "xls", "xlsm"]
)

if uploaded_file is not None:
    with st.spinner("Parsing data..."):
        df = clean_and_parse_data(uploaded_file)

    st.caption(f"Parsed sheet `{SOURCE_SHEET_NAME}` after skipping the first two rows.")

    st.subheader("Data Overview")
    st.dataframe(
        df.style.format(
            formatter={
                col: "{:,.0f}"
                for col in df.columns
                if pd.api.types.is_numeric_dtype(df[col])
            }
        ),
        width="stretch",
        hide_index=True,
    )

    guessed_lob_counts = (
        df["LoB"]
        .value_counts(dropna=False)
        .rename_axis("LoB")
        .reset_index(name="Claims")
    )
    st.subheader("Guessed LoB Summary")
    st.dataframe(guessed_lob_counts, width="stretch", hide_index=True)

    st.subheader("Generate LaTeX Document Section")

    if st.button("Generate LaTeX Code"):
        with st.spinner("Generating LaTeX template..."):
            # processing all lobs one by one and saving everything in separated files
            for lob in LOB_MAPPING.keys():
                df_latex, escaped_columns = format_for_latex(df, lob=lob)
                # rows_data = df_latex.values.tolist()
                if df_latex.empty:
                    latex_code = (
                        """\\subsection*{Potential Large Losses Without Reserve for """
                        + lob
                        + """}
                        
                        No potential large losses without reserve for """
                        + lob
                        + """.
                        """
                    )
                else:
                    jinja_template = Template(LATEX_TEMPLATE)
                    latex_code = jinja_template.render(
                        rows=df_latex.to_dict(orient="records"), lob=lob
                    )

                output_path = export_latex_to_file(latex_code, lob=lob)
                st.success(f"LaTeX code generated successfully in {output_path.name}.")
                st.code(latex_code, language="latex")
            st.download_button(
                label="Download .tex file",
                data=latex_code,
                file_name="claims_update.tex",
                mime="text/plain",
            )
else:
    st.info("Please upload an Excel file to get started.")
