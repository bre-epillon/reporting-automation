import subprocess
from pathlib import Path

import streamlit as st


def compile_latex_to_pdf(tex_filepath, output_stem=None):
    """Compile a LaTeX file and return the generated PDF path."""
    tex_path = Path(tex_filepath).resolve()
    pdf_stem = output_stem or tex_path.stem
    pdf_path = tex_path.with_name(f"{pdf_stem}.pdf")
    command = [
        "pdflatex",
        "-interaction=nonstopmode",
        f"-jobname={pdf_stem}",
        tex_path.name,
    ]

    try:
        for _ in range(2):
            subprocess.run(
                command,
                check=True,
                cwd=tex_path.parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        return pdf_path if pdf_path.exists() else None
    except subprocess.CalledProcessError as exc:
        if pdf_path.exists():
            return pdf_path

        error_output = (
            exc.stderr.decode("utf-8", errors="ignore")
            or exc.stdout.decode("utf-8", errors="ignore")
        )
        st.error(
            "LaTeX Compilation Failed: "
            f"{error_output}"
        )
        return None
    except FileNotFoundError:
        st.error("LaTeX Compilation Failed: `pdflatex` is not available on PATH.")
        return None
