# Chapter 2: Input Parameters — exact LaTeX template match


from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_CB_LOAD,
    KEY_CB_TYPE,
    KEY_CROSS_BRACING,
    KEY_DECK_CONCRETE_GRADE_BASIC,
    KEY_DESIGN_MODE,
    KEY_DO_GAMMA_C_BASIC,
    KEY_DO_GAMMA_FLT,
    KEY_DO_GAMMA_M0,
    KEY_DO_GAMMA_M1,
    KEY_DO_GAMMA_MF,
    KEY_DO_GAMMA_S,
    KEY_DO_GAMMA_V,
    KEY_END_DIAPHRAGM,
    KEY_FOOTPATH,
    KEY_GIRDER,
    KEY_INCLUDE_MEDIAN,
    KEY_MD_TYPE,
    KEY_MP_CB_BRACING_SECTION_DESIGNATION,
    KEY_MP_CB_MEMBER_ID,
    KEY_MP_CB_SELECT_GIRDERS,
    KEY_MP_CB_SPACING,
    KEY_MP_CB_TYPE,
    KEY_MP_ED_BRACING_SECTION_DESIGNATION,
    KEY_MP_ED_MEMBER_ID,
    KEY_MP_ED_SELECT_GIRDERS,
    KEY_MP_ED_TYPE,
    KEY_MP_GD_MEMBER_ID,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
    KEY_MP_GIRDER_DEPTH,
    KEY_MP_GIRDER_SYMMETRY,
    KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
    KEY_MP_GIRDER_TORSIONAL_RESTRAINT,
    KEY_MP_GIRDER_TYPE,
    KEY_MP_GIRDER_WARPING_RESTRAINT,
    KEY_MP_GIRDER_WEB_THICKNESS,
    KEY_MP_GIRDER_WEB_TYPE,
    KEY_MP_STIFFENER_BEARING_THICKNESS,
    KEY_MP_STIFFENER_INTERMEDIATE,
    KEY_MP_STIFFENER_INTERMEDIATE_SPACING,
    KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS,
    KEY_MP_STIFFENER_LONGITUDINAL,
    KEY_MP_STIFFENER_NO_BEARING_STIFFENERS,
    KEY_MP_STIFFENER_SPACING,
    KEY_RL_LOAD_VALUE,
    KEY_RL_TYPE,
    KEY_SD_SHEAR_DIAMETER,
    KEY_SD_SHEAR_HEIGHT,
    KEY_SD_SHEAR_STUDS_PER_SECTION,
    KEY_SD_SHEAR_ULTIMATE_STRENGTH,
    KEY_SD_SHEAR_YIELD_STRENGTH,
    KEY_SKEW_ANGLE,
    KEY_SPAN,
    KEY_STRUCTURE_TYPE,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_OVERALL_WIDTH,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS
)

from osdagbridge.core.reports.report_utils import _render_value, get_girder_entries, _tex

def ch2_input_parameters(m, input_dict, output_dict=None):
    girder_entries = get_girder_entries(input_dict)
    n_girders = len(girder_entries)
    # Median row only shown when the user included a median
    median_row = ""
    if str(input_dict.get(KEY_INCLUDE_MEDIAN, "")).strip().lower() in ("yes", "true", "1"):
        median_row = (r"\textnormal{Median Type} & "
                      + _render_value(input_dict, KEY_MD_TYPE)
                      + r""" \\[6pt]
\hline
""")

    # Location & environmental data extraction
    loc_data = input_dict.get("project.location") or input_dict.get("location") or {}
    if isinstance(loc_data, str):
        try:
            import ast
            loc_data = ast.literal_eval(loc_data)
        except Exception:
            try:
                import json
                loc_data = json.loads(loc_data)
            except Exception:
                loc_data = {}
    weather = loc_data.get("weather_data", {}) if isinstance(loc_data, dict) else {}
    lat_val = weather.get("latitude") or input_dict.get("latitude")
    lon_val = weather.get("longitude") or input_dict.get("longitude")
    lat_lon_str = f"{lat_val}° N, {lon_val}° E" if lat_val and lon_val else (f"{lat_val}, {lon_val}" if lat_val or lon_val else "Not provided")

    zone_val = weather.get("zone") or input_dict.get("loading.seismic_load.computed.zone_factor")
    z_num = weather.get("z_value") or input_dict.get("loading.seismic_load.computed.zone_factor")
    if zone_val and z_num:
        seismic_zone_str = f"Zone {zone_val} (Z = {z_num})"
    elif z_num:
        seismic_zone_str = f"Zone Factor Z = {z_num}"
    elif zone_val:
        seismic_zone_str = f"Zone {zone_val}"
    else:
        seismic_zone_str = "Not provided"

    wind_speed_val = weather.get("wind_speed") or input_dict.get("loading.wind_load.basic_wind_speed") or input_dict.get("wind_speed")
    wind_speed_str = f"{wind_speed_val} m/s" if wind_speed_val else "Not provided"

    max_temp_val = weather.get("max_temp") or input_dict.get("shade_temp_max")
    min_temp_val = weather.get("min_temp") or input_dict.get("shade_temp_min")
    if max_temp_val is not None and min_temp_val is not None:
        shade_temp_str = f"{max_temp_val} °C / {min_temp_val} °C"
    else:
        shade_temp_str = "Not provided"

    rl_type_str = _render_value(input_dict, KEY_RL_TYPE)
    if not rl_type_str or rl_type_str.strip() in ("", "None", "---"):
        rl_type_str = "None (Crash barrier provided)"
    rl_load_str = _render_value(input_dict, KEY_RL_LOAD_VALUE)
    if not rl_load_str or rl_load_str.strip() in ("", "None", "---"):
        rl_load_str = "N/A"

    # Traffic lanes (IRC 5 Cl. 104.3.1)
    lanes_val = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)
    if not lanes_val or str(lanes_val).strip() in ("", "None", "0"):
        try:
            cw = float(input_dict.get(KEY_CARRIAGEWAY_WIDTH, 7.0))
            lanes_str = "2" if cw >= 5.3 else "1"
        except Exception:
            lanes_str = "2"
    else:
        lanes_str = str(lanes_val).strip()

    # Footpath width display
    fp_prov_val = str(input_dict.get(KEY_FOOTPATH, "None")).strip()
    fp_w_val = input_dict.get(KEY_TS_FOOTPATH_WIDTH)
    if fp_prov_val.lower() in ("none", "no", "") or (fp_w_val is not None and str(fp_w_val).strip() in ("0", "0.0", "0.00")):
        fp_width_display = "0.0 m (No footpath provided)"
    else:
        fp_width_display = f"{_render_value(input_dict, KEY_TS_FOOTPATH_WIDTH, ' m')} (IRC 5 Cl. 104.3.6 min: 1.5 m)"

    return r"""
\chapter{Input Parameters}

\setlength{\abovecaptionskip}{2pt}
\setlength{\belowcaptionskip}{2pt}

This section documents all inputs provided to OsdagBridge. User-provided inputs are clearly distinguished from software-assumed defaults. Where the user did not supply a value, the software has applied the IRC/IS code default or an empirical guideline; these are annotated with an asterisk (\sdstar{}).

\section{Basic Inputs (User-Defined)}
\label{sec:basic-inputs}

\noindent\textit{Note: These inputs are mandatory and were provided by the user.}

\begin{table}[H]
\caption{\textbf{Project Location}}
\label{subsec:project-location}
\begin{tabular}{|L{5.5cm}|L{8.5cm}|}
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\textnormal{Project Location} & """ + _tex(m.project_location) + r""" \\
\hline
\textnormal{Latitude / Longitude} & """ + _tex(lat_lon_str) + r""" \\
\hline
\textnormal{Seismic Zone (IRC 6)} & """ + _tex(seismic_zone_str) + r""" \\
\hline
\textnormal{Basic Wind Speed (IRC 6)} & """ + _tex(wind_speed_str) + r""" \\
\hline
\textnormal{Shade Temp. Max / Min (IRC 6)} & """ + _tex(shade_temp_str) + r""" \\
\hline
\end{tabular}
\vspace{0.4cm}
\end{table}

\begin{table}[H]
\caption{\textbf{Bridge Geometry}}
\label{subsec:bridge-geometry}
\begin{tabular}{|L{5.5cm}|L{8.5cm}|}
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\textnormal{Type of Structure} & """ + (_render_value(input_dict, KEY_STRUCTURE_TYPE)) + r""" \\
\hline
\textnormal{Span (m)} & """ + (_render_value(input_dict, KEY_SPAN, ' m')) + r""" \\
\hline
\textnormal{Carriageway Width (m)} & """ + (_render_value(input_dict, KEY_CARRIAGEWAY_WIDTH, ' m')) + r""" \\
\hline
\textnormal{Include Median} & """ + (_render_value(input_dict, KEY_INCLUDE_MEDIAN)) + r""" \\
\hline
\textnormal{Footpath} & """ + (_render_value(input_dict, KEY_FOOTPATH)) + r""" \\
\hline
\textnormal{Skew Angle (degrees)} & """ + (_render_value(input_dict, KEY_SKEW_ANGLE, '°')) + r""" (IRC 24 Cl. 504.8 limit: $\pm$15°) \\
\hline
\end{tabular}
\end{table}
\vspace{0.4cm}

\begin{table}[H]
\caption{\textbf{Material Selection}}
\label{subsec:material}
\begin{tabular}{|L{5.5cm}|L{8.5cm}|}
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\textnormal{Girder Steel Grade (IS 2062)} & """ + (_render_value(input_dict, KEY_GIRDER)) + r""" \\
\hline
\textnormal{Cross Bracing Steel Grade} & """ + (_render_value(input_dict, KEY_CROSS_BRACING)) + r""" \\
\hline
\textnormal{End Diaphragm Steel Grade} & """ + (_render_value(input_dict, KEY_END_DIAPHRAGM)) + r""" \\
\hline
\textnormal{Concrete Deck Grade (IRC 22)} & """ + (_render_value(input_dict, KEY_DECK_CONCRETE_GRADE_BASIC)) + r""" \\
\hline
\end{tabular}
\end{table}
\vspace{0.4cm}

\newpage
\section{Additional Inputs}
\label{sec:additional-inputs}

Where the user has modified additional inputs, those values are reported here. Where no modification was made, the software default is shown.

\vspace{0.8cm}

\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Typical Section Details}} \\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endfirsthead
\multicolumn{2}{c}{{\bfseries Typical Section Details (continued)}} \\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endhead
\hline
\multicolumn{2}{r}{\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
\textnormal{Overall Bridge Width (m)} & """ + (_render_value(input_dict, KEY_TS_OVERALL_WIDTH)) + r""" \\[6pt]
\hline
\textnormal{No. of Girders} & """ + (_render_value(input_dict, KEY_TS_NO_OF_GIRDERS)) + r""" \\[6pt]
\hline
\textnormal{Girder Spacing (m)} & """ + (_render_value(input_dict, KEY_TS_GIRDER_SPACING, ' m')) + r""" \\[6pt]
\hline
\textnormal{Deck Overhang Width (m)} & """ + (_render_value(input_dict, KEY_TS_DECK_OVERHANG, ' m')) + r""" \\[6pt]
\hline
\textnormal{Deck Thickness (mm)} & """ + (_render_value(input_dict, KEY_TS_DECK_THICKNESS, ' mm')) + r""" \\[6pt]
\hline
\textnormal{Footpath Width (m)} & """ + fp_width_display + r""" \\[6pt]
\hline
\textnormal{No. of Traffic Lanes} & """ + lanes_str + r""" (per IRC 5 Cl. 104.3.1) \\[6pt]
\hline
\end{longtable}

\vspace{0.8em}

\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Components Details}} \\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endfirsthead
\multicolumn{2}{c}{{\bfseries Components Details (continued)}} \\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endhead
\hline
\multicolumn{2}{r}{\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
\textnormal{Crash Barrier Type} & """ + (_render_value(input_dict, KEY_CB_TYPE)) + r""" \\[6pt]
\hline
\textnormal{Crash Barrier Load (kN/m)} & """ + (_render_value(input_dict, KEY_CB_LOAD)) + r""" \\[6pt]
\hline
""" + median_row + r"""
\textnormal{Railing Type} & """ + (_render_value(input_dict, KEY_RL_TYPE)) + r""" \\[6pt]
\hline
\textnormal{Railing Load (kN/m)} & """ + (_render_value(input_dict, KEY_RL_LOAD_VALUE)) + r""" \\[6pt]
\hline
\textnormal{Wearing Course Material} & """ + (_render_value(input_dict, KEY_WC_MATERIAL)) + r""" \\[6pt]
\hline
\textnormal{Wearing Course Thickness (mm)} & """ + (_render_value(input_dict, KEY_WC_THICKNESS, ' mm')) + r""" \\[6pt]
\hline
\end{longtable}

""" + _girder_tables(input_dict, n_girders) + r"""

""" + _bracing_tables(input_dict, n_girders) + r"""

""" + _shear_connector_table(input_dict, output_dict) + r"""

""" + _safety_factors_table(input_dict)


def _girder_tables(input_dict, n_girders):
    # Fetch backend-populated labels via exact suffix pattern (defaults.py)
    # KEY_MP_GD_SELECT_GIRDER.G{i}    = 'G{i}'
    # KEY_MP_GD_MEMBER_ID.G{i}.M1     = 'G{i}M1'
    # All other girder/stiffener keys: {BASE_KEY}.G{i}.M1
    n = n_girders if n_girders >= 1 else 1
    girder_entries = get_girder_entries(input_dict)
    if not girder_entries:
        girder_entries = [(f"Girder {i}", f"M1") for i in range(1, n + 1)]
    
    entries_for_table = [
        (lbl, mid, i)
        for i, (lbl, mid) in enumerate(
            girder_entries,
            start=1,
        )
    ]

    def _dim_val(base_key, i):
        val = input_dict.get(f"{base_key}.G{i}.M1")
        if val in ("", None):
            return ""
        try:
            f = float(val)
            if f < 20.0:  # stored in meters in internal grillage model
                f *= 1000.0
            return f"{f:.1f}"
        except (ValueError, TypeError):
            return _tex(str(val))

    # Helper: one girder-dimension row
    def _dim_row(g_lbl, i):
        d_val = _dim_val(KEY_MP_GIRDER_DEPTH, i)
        tw_val = _dim_val(KEY_MP_GIRDER_WEB_THICKNESS, i)
        tfw_val = _dim_val(KEY_MP_GIRDER_TOP_FLANGE_WIDTH, i)
        tft_val = _dim_val(KEY_MP_GIRDER_TOP_FLANGE_THICKNESS, i)
        bfw_val = _dim_val(KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH, i)
        bft_val = _dim_val(KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS, i)
        return (g_lbl + r""" & """
                + (f"{d_val} mm" if d_val else "")
                + r""" & """
                + (f"{tw_val} mm" if tw_val else "")
                + r""" & """
                + (f"{tfw_val} mm, {tft_val} mm" if tfw_val and tft_val else "")
                + r""" & """
                + (f"{bfw_val} mm, {bft_val} mm" if bfw_val and bft_val else "")
                + r""" \\[8pt]
\hline
""")

    # Helper: one general-info row
    def _gen_row(g_lbl, m_id, i):
        return (g_lbl + r""" & """ + m_id + r""" & """
                + (_render_value(input_dict, KEY_DESIGN_MODE))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_GIRDER_TYPE}.G{i}.M1"))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_GIRDER_SYMMETRY}.G{i}.M1"))
                + r""" \\[8pt]
\hline
""")

    # Helper: one restraint/stiffener row
    def _rst_row(g_lbl, i):
        return (g_lbl + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_GIRDER_TORSIONAL_RESTRAINT}.G{i}.M1"))
                + ', '
                + (_render_value(input_dict, f"{KEY_MP_GIRDER_WARPING_RESTRAINT}.G{i}.M1"))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_GIRDER_WEB_TYPE}.G{i}.M1"))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_STIFFENER_INTERMEDIATE}.G{i}.M1"))
                + '; Spacing: '
                + (_render_value(input_dict, f"{KEY_MP_STIFFENER_INTERMEDIATE_SPACING}.G{i}.M1", ' mm'))
                + '; Thickness: '
                + (_render_value(input_dict, f"{KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS}.G{i}.M1", ' mm'))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_STIFFENER_LONGITUDINAL}.G{i}.M1"))
                + r""" & No.: """
                + (_render_value(input_dict, f"{KEY_MP_STIFFENER_NO_BEARING_STIFFENERS}.G{i}.M1"))
                + '; Spacing: '
                + (_render_value(input_dict, f"{KEY_MP_STIFFENER_SPACING}.G{i}.M1", ' mm'))
                + '; Thickness: '
                + (_render_value(input_dict, f"{KEY_MP_STIFFENER_BEARING_THICKNESS}.G{i}.M1", ' mm'))
                + r""" \\[8pt]
\hline
""")

    gen_rows = "".join([_gen_row(g_lbl, m_id, i) for g_lbl, m_id, i in entries_for_table])
    dim_rows = "".join([_dim_row(g_lbl, i) for g_lbl, _, i in entries_for_table])
    rst_rows = "".join([_rst_row(g_lbl, i) for g_lbl, _, i in entries_for_table])

    return (r"""
\newpage

\vspace{0.4em}
\noindent
            
\vspace{4pt}
\begin{longtable}{|L{2.2cm}|L{1.8cm}|p{3.8cm}|p{3.8cm}|p{3.8cm}|}
\caption{\textbf{Girder General Information}} \\
\hline
\textbf{Girder} & \textbf{Member ID} & \textbf{Design Mode} & \textbf{Girder Type} & \textbf{Girder Symmetry} \\[6pt]
\hline
\endfirsthead
\multicolumn{5}{c}{{\bfseries Girder General Information (continued)}} \\
\hline
\textbf{Girder} & \textbf{Member ID} & \textbf{Design Mode} & \textbf{Girder Type} & \textbf{Girder Symmetry} \\[6pt]
\hline
\endhead
\hline
\multicolumn{5}{r}{\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
"""
            + gen_rows
            + r"""\end{longtable}

\vspace{0.6em}

\vspace{4pt}
\begin{longtable}{|L{2.0cm}|L{2.5cm}|L{2.5cm}|p{4.2cm}|p{4.2cm}|}
\caption{\textbf{Girder Section Dimensions}} \\
\hline
\textbf{Girder} & \textbf{Total Depth, D} & \textbf{Web, $t_w$} & \textbf{Top Flange ($b_{tf}, t_{tf}$)} & \textbf{Bottom Flange ($b_{bf}, t_{bf}$)} \\[6pt]
\hline
\endfirsthead
\multicolumn{5}{c}{{\bfseries Girder Section Dimensions (continued)}} \\
\hline
\textbf{Girder} & \textbf{Total Depth, D} & \textbf{Web, $t_w$} & \textbf{Top Flange ($b_{tf}, t_{tf}$)} & \textbf{Bottom Flange ($b_{bf}, t_{bf}$)} \\[6pt]
\hline
\endhead
\hline
\multicolumn{5}{r}{\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
"""
            + dim_rows
            + r"""\end{longtable}

\vspace{0.6em}

\vspace{4pt}
\begin{longtable}{|L{1.4cm}|p{2.2cm}|p{2.2cm}|p{3.0cm}|p{2.4cm}|p{2.2cm}|}
\caption{\textbf{Girder Restraint and Stiffener Details}} \\
\hline
\textbf{Girder} & \textbf{Torsional / Warping Restraint} & \textbf{Web Philosophy} & \textbf{Intermediate Stiffeners} & \textbf{Longitudinal Stiffeners} & \textbf{Bearing Stiffener} \\[6pt]
\hline
\endfirsthead
\multicolumn{6}{c}{{\bfseries Girder Restraint and Stiffener Details (continued)}} \\
\hline
\textbf{Girder} & \textbf{Torsional / Warping Restraint} & \textbf{Web Philosophy} & \textbf{Intermediate Stiffeners} & \textbf{Longitudinal Stiffeners} & \textbf{Bearing Stiffener} \\[6pt]
\hline
\endhead
\hline
\multicolumn{6}{r}{\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
"""
            + rst_rows
            + r"""\end{longtable}
""")


def _bracing_tables(input_dict, n_girders):
    n = n_girders if n_girders >= 2 else 2
    panels = [
        (
            _render_value(input_dict, f"{KEY_MP_CB_SELECT_GIRDERS}.G{i}G{i+1}.B{i}M1"),
            _render_value(input_dict, f"{KEY_MP_CB_MEMBER_ID}.G{i}G{i+1}.B{i}M1"),
            _render_value(input_dict, f"{KEY_MP_ED_SELECT_GIRDERS}.G{i}G{i+1}.E{i}M1"),
            _render_value(input_dict, f"{KEY_MP_ED_MEMBER_ID}.G{i}G{i+1}.E{i}M1"),
            i
        )
        for i in range(1, n)
    ]

    # Helper: one cross-bracing row (all locations share same bracing config)
    def _cb_row(location, member_ids, i):
        return (location + r""" & """ + member_ids + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_CB_TYPE}.G{i}G{i+1}.B{i}M1"))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_CB_BRACING_SECTION_DESIGNATION}.G{i}G{i+1}.B{i}M1"))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_CB_SPACING}.G{i}G{i+1}.B{i}M1", ' m'))
                + r""" \\[6pt]
\hline
""")

    # Helper: one end-diaphragm row (all locations share same config)
    def _ed_row(location, member_ids, i):
        return (location + r""" & """ + member_ids + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_ED_TYPE}.G{i}G{i+1}.E{i}M1"))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_ED_BRACING_SECTION_DESIGNATION}.G{i}G{i+1}.E{i}M1"))
                + r""" \\[6pt]
\hline
""")

    cb_rows = "".join([_cb_row(cb_loc, cb_ids, i) for cb_loc, cb_ids, _, _, i in panels])
    ed_rows = "".join([_ed_row(ed_loc, ed_ids, i) for _, _, ed_loc, ed_ids, i in panels])

    return (r"""
\newpage

\vspace{0.4em}
\setlength{\tabcolsep}{4pt}
\setlength\LTleft{0pt}
\setlength\LTright{\fill}

\begin{longtable}{|L{2.5cm}|L{2.5cm}|L{3.5cm}|L{3.5cm}|C{2.5cm}|}
\caption{\textbf{Member Properties: Cross Bracing Details}} \\
\hline
\textbf{Location} & \textbf{Member IDs} & \textbf{Type of Bracing} & \textbf{Bracing Section} & \textbf{Spacing (m)} \\
\hline
\endfirsthead
\multicolumn{5}{c}{{\bfseries Member Properties: Cross Bracing Details (continued)}} \\
\hline
\textbf{Location} & \textbf{Member IDs} & \textbf{Type of Bracing} & \textbf{Bracing Section} & \textbf{Spacing (m)} \\
\hline
\endhead
\hline
\multicolumn{5}{r}{\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
"""
+ cb_rows
+ r"""\end{longtable}

\vspace{0.4em}
\noindent
\setlength{\tabcolsep}{4pt}
\setlength\LTleft{0pt}
\setlength\LTright{\fill}

\begin{longtable}{|L{3.0cm}|L{3.0cm}|L{4.0cm}|L{4.5cm}|}
\caption{\textbf{Member Properties: End Diaphragm Details}} \\
\hline
\textbf{Location} & \textbf{Member IDs} & \textbf{Type of Bracing} & \textbf{Bracing Section} \\
\hline
\endfirsthead
\multicolumn{4}{c}{{\bfseries Member Properties: End Diaphragm Details (continued)}} \\
\hline
\textbf{Location} & \textbf{Member IDs} & \textbf{Type of Bracing} & \textbf{Bracing Section} \\
\hline
\endhead
\hline
\multicolumn{4}{r}{\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
"""
+ ed_rows
+ r"""\end{longtable}
""")


def _shear_connector_table(input_dict, output_dict=None):
    # Stud computed properties live in output_dict (populated by store_design_results)
    od = output_dict or {}
    return r"""
\label{subsec:shear-connectors}

\vspace{2.2em}

\vspace{0.4em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Shear Connector Details}} \\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endfirsthead
\multicolumn{2}{c}{{\bfseries Shear Connector Details (continued)}} \\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endhead
\hline
\multicolumn{2}{r}{\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
\textnormal{Stud Diameter (mm)} & """ + (_render_value(od, KEY_SD_SHEAR_DIAMETER, ' mm')) + r""" \\[6pt]
\hline
\textnormal{Stud Height (mm)} & """ + (_render_value(od, KEY_SD_SHEAR_HEIGHT, ' mm')) + r""" \\[6pt]
\hline
\textnormal{Stud $f_y$ (MPa)} & """ + (_render_value(od, KEY_SD_SHEAR_YIELD_STRENGTH, ' MPa')) + r""" \\[6pt]
\hline
\textnormal{Stud $f_u$ (MPa)} & """ + (_render_value(od, KEY_SD_SHEAR_ULTIMATE_STRENGTH, ' MPa')) + r""" \\[6pt]
\hline
\textnormal{No. of Studs per Section} & """ + (_render_value(od, KEY_SD_SHEAR_STUDS_PER_SECTION)) + r""" \\[6pt]
\hline
\end{longtable}
"""

def _safety_factors_table(input_dict):
    return r"""
\label{subsec:safety-factors}

\vspace{2.2em}

\vspace{0.3em}
\noindent\textit{Note: All values are per IRC 22 Table 1 unless user-modified.}

\vspace{0.4em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Partial Safety Factors}} \\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endfirsthead
\multicolumn{2}{c}{{\bfseries Partial Safety Factors (continued)}} \\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endhead
\hline
\multicolumn{2}{r}{\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
\textnormal{$\gamma_{M0}$ (Yielding / Buckling)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_M0)) + r""" \\[6pt]
\hline
\textnormal{$\gamma_{M1}$ (Ultimate Stress)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_M1)) + r""" \\[6pt]
\hline
\textnormal{$\gamma_C$ (Concrete, Basic)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_C_BASIC)) + r""" \\[6pt]
\hline
\textnormal{$\gamma_s$ (Reinforcement)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_S)) + r""" \\[6pt]
\hline
\textnormal{$\gamma_v$ (Shear Connectors)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_V)) + r""" \\[6pt]
\hline
\textnormal{$\gamma_{fft}$ (Fatigue Load)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_FLT)) + r""" \\[6pt]
\hline
\textnormal{$\gamma_{Mft}$ (Fatigue Strength)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_MF)) + r""" \\[6pt]
\hline
\end{longtable}
"""

