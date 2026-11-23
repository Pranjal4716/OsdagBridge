# =============================================================================
# OsdagBridge — Centralized LaTeX Report Styles & Theme
# =============================================================================

from typing import List, Optional

# ── Color Palette ────────────────────────────────────────────────────────────
OSDAG_GREEN = "#91B014"
COLOR_PRIMARY = "#91B014"
COLOR_TEXT = "#222222"
COLOR_MUTED = "#666666"
COLOR_PASS = "#2E7D32"      # Forest Green
COLOR_FAIL = "#C62828"      # Crimson Red
COLOR_THRESHOLD = "#D32F2F" # Red dashed threshold
COLOR_HEADER_BG = "#F5F5F5"
COLOR_BORDER = "#BDBDBD"

# Chart colors for matplotlib
CHART_COLORS = {
    "girders": "#1F77B4",       # Steel Blue
    "top_bracing": "#2CA02C",   # Green
    "bot_bracing": "#17BECF",   # Cyan
    "diag_bracing": "#FF7F0E",  # Orange
    "diaphragms": "#9467BD",    # Purple
    "shear_connectors": "#8C564B", # Brown
    "concrete": "#7F7F7F",      # Concrete Grey
    "rebar": "#D62728",         # Steel Rebar Red
    "pass": "#2E7D32",
    "fail": "#C62828",
}

# ── LaTeX Preamble Configuration ─────────────────────────────────────────────
GEOMETRY_OPTIONS = r"a4paper, top=1.0in, bottom=1.15in, left=1.0in, right=1.0in, headheight=16pt, headsep=14pt, footskip=28pt"

TABLE_STYLE_PREAMBLE = r"""
% Table layout and spacing: consistent padding, row height, and longtable skips
\setlength{\tabcolsep}{6pt}
\renewcommand{\arraystretch}{1.12}
\setlength{\LTpre}{4pt}
\setlength{\LTpost}{6pt}
\setlength{\arrayrulewidth}{0.5pt}
\setlength{\extrarowheight}{0.6pt}

% Prevent orphan table headers
\BeforeBeginEnvironment{table}{\needspace{5\baselineskip}}
\BeforeBeginEnvironment{longtable}{\needspace{5\baselineskip}}

% Custom column alignments with text wrapping
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}p{#1}}

% Safe Unicode declarations for symbols commonly produced by engineering routines
\DeclareUnicodeCharacter{2264}{\ensuremath{\le}}
\DeclareUnicodeCharacter{2265}{\ensuremath{\ge}}
\DeclareUnicodeCharacter{00B1}{\ensuremath{\pm}}
\DeclareUnicodeCharacter{00B0}{\ensuremath{^\circ}}
\DeclareUnicodeCharacter{00B2}{\ensuremath{^2}}
\DeclareUnicodeCharacter{00B3}{\ensuremath{^3}}
\DeclareUnicodeCharacter{00D7}{\ensuremath{\times}}
\DeclareUnicodeCharacter{03BC}{\ensuremath{\mu}}
\DeclareUnicodeCharacter{03C3}{\ensuremath{\sigma}}
\DeclareUnicodeCharacter{03B5}{\ensuremath{\varepsilon}}
\DeclareUnicodeCharacter{03C1}{\ensuremath{\rho}}
\DeclareUnicodeCharacter{2014}{--}
\DeclareUnicodeCharacter{2013}{-}
"""

# ── LongTable Helper Functions ───────────────────────────────────────────────

def make_longtable_header(
    caption: str,
    col_spec: str,
    header_cells: List[str],
    label: str = "",
    cont_caption: Optional[str] = None
) -> str:
    """
    Generate a robust, multi-page LaTeX LongTable header with:
    - Proper caption formatting ending in `\\\\` (prevents misplaced \\noalign).
    - `\\endfirsthead` for the initial page.
    - Repeated table headers on every continuation page via `\\endhead`.
    - Continuation notice footer via `\\endfoot`.
    - Final rule via `\\endlastfoot`.
    """
    n_cols = len(header_cells)
    lbl_tex = f"\\label{{{label}}}" if label else ""
    header_row = " & ".join(f"\\textbf{{{cell}}}" for cell in header_cells) + r" \\[6pt]"
    cont_text = cont_caption or f"{caption} (continued from previous page)"

    return (
        f"\\begin{{longtable}}{{{col_spec}}}\n"
        f"\\caption{{\\textbf{{{caption}}}}}{lbl_tex} \\\\\n"
        f"\\hline\n"
        f"{header_row}\n"
        f"\\hline\n"
        f"\\endfirsthead\n\n"
        f"\\multicolumn{{{n_cols}}}{{c}}{{\\bfseries {cont_text}}} \\\\\n"
        f"\\hline\n"
        f"{header_row}\n"
        f"\\hline\n"
        f"\\endhead\n\n"
        f"\\hline\n"
        f"\\multicolumn{{{n_cols}}}{{r}}{{\\textit{{Continued on next page...}}}} \\\\\n"
        f"\\endfoot\n\n"
        f"\\hline\n"
        f"\\endlastfoot\n"
    )


def make_longtable_footer() -> str:
    """Close the longtable environment cleanly."""
    return "\\end{longtable}\n"
