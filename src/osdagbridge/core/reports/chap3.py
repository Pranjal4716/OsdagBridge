# =============================================================================
# Chapter 3: Loads and Load Combinations
# Extracted from report_generator.py — DO NOT add business logic here.
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_CB_LOAD,
    KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_IRC_CLASS_SV,
    KEY_MATERIAL_DECK_DENSITY,
    KEY_MATERIAL_GIRDER_DENSITY,
    KEY_PL_SELF_WEIGHT_FACTOR,
    KEY_RL_LOAD_VALUE,
    KEY_SL_DAMPING,
    KEY_SL_DEAD_LOAD_MODE,
    KEY_SL_DEAD_LOAD_VALUE,
    KEY_SL_HORIZONTAL_COEFF,
    KEY_SL_IMPORTANCE_FACTOR,
    KEY_SL_LIVE_LOAD_MODE,
    KEY_SL_LIVE_LOAD_VALUE,
    KEY_SL_SEISMIC_ZONE,
    KEY_SL_SOIL_TYPE,
    KEY_SL_SPECTRAL_COEFF,
    KEY_SL_TIME_PERIOD,
    KEY_SL_VERTICAL_COEFF,
    KEY_SL_ZONE_FACTOR,
    KEY_SPAN,
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_HIGHEST_MAX_TEMP,
    KEY_TL_LOWEST_MIN_TEMP,
    KEY_TL_TEMP_FALL,
    KEY_TL_TEMP_RISE,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS,
    KEY_WL_AVG_EXPOSED_HEIGHT,
    KEY_WL_BASIC_WIND_SPEED,
    KEY_WL_HOURLY_MEAN_WIND,
    KEY_WL_HOURLY_WIND_PRESSURE,
    KEY_WL_LONGITUDINAL_WIND_FORCE,
    KEY_WL_TERRAIN_TYPE,
    KEY_WL_TRANSVERSE_WIND_FORCE,
    KEY_WL_VERTICAL_WIND_FORCE
)

from osdagbridge.core.reports.report_utils import _tex, _render_value

def ch3_loads(input_dict):
    # Live load vehicle names mapping
    vehicles = []
    if input_dict.get(KEY_LL_IRC_CLASS_A):
        vehicles.append("Class A")
    if input_dict.get(KEY_LL_IRC_70R_WHEELED):
        vehicles.append("Class 70R (Wheeled)")
    if input_dict.get(KEY_LL_IRC_70R_TRACKED):
        vehicles.append("Class 70R (Tracked)")
    if input_dict.get(KEY_LL_IRC_AA_WHEELED):
        vehicles.append("Class AA (Wheeled)")
    if input_dict.get(KEY_LL_IRC_AA_TRACKED):
        vehicles.append("Class AA (Tracked)")
    if input_dict.get(KEY_LL_IRC_CLASS_SV):
        vehicles.append("Class SV")
    if input_dict.get(KEY_LL_IRC_70R_BOGIE):
        vehicles.append("Class 70R (Bogie)")
    if input_dict.get(KEY_LL_IRC_CLASS_FATIGUE):
        vehicles.append("Class Fatigue")
    
    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if custom and isinstance(custom, list):
        for c in custom:
            if isinstance(c, dict) and c.get('name'):
                vehicles.append(c['name'])
            elif isinstance(c, str):
                vehicles.append(c)
                
    vehicles_str = ", ".join(vehicles) if vehicles else "None"

    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
    span = input_dict.get(KEY_SPAN)
    impact_factor_str = ""
    if span not in (None, ""):
        try:
            span_m = float(span)
            factors = []
            if input_dict.get(KEY_LL_IRC_CLASS_A):
                im_a = IRC6_2017.cl_208_2_impact_factor(span_m)
                factors.append(f"Class A: {1.0 + im_a:.3f}")
            is_wheeled_heavy = (
                input_dict.get(KEY_LL_IRC_70R_WHEELED) or 
                input_dict.get(KEY_LL_IRC_AA_WHEELED) or 
                input_dict.get(KEY_LL_IRC_70R_BOGIE)
            )
            is_tracked_heavy = (
                input_dict.get(KEY_LL_IRC_70R_TRACKED) or 
                input_dict.get(KEY_LL_IRC_AA_TRACKED)
            )
            if is_wheeled_heavy or is_tracked_heavy:
                im_aa = IRC6_2017.cl_208_3_impact_factor(span_m)
                factors.append(f"Class AA/70R: {1.0 + im_aa:.3f}")
            
            if factors:
                impact_factor_str = ", ".join(factors)
            else:
                impact_factor_str = "N/A"
        except Exception:
            impact_factor_str = "N/A"
    else:
        impact_factor_str = "N/A"

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

    # Wind parameters (Table 3.5)
    vb_val = input_dict.get(KEY_WL_BASIC_WIND_SPEED) or weather.get("wind_speed") or input_dict.get("wind_speed")
    terrain_val = input_dict.get(KEY_WL_TERRAIN_TYPE) or "Plain Terrain"
    h_val = input_dict.get(KEY_WL_AVG_EXPOSED_HEIGHT) or "10"

    vz_val = input_dict.get(KEY_WL_HOURLY_MEAN_WIND)
    pz_val = input_dict.get(KEY_WL_HOURLY_WIND_PRESSURE)
    if (not vz_val or not pz_val) and vb_val:
        try:
            t_map = {"Plain Terrain": "plain", "Terrain with Obstructions": "obstructed"}
            w_res = IRC6_2017.table_12(float(h_val), t_map.get(str(terrain_val), "plain"), float(vb_val))
            vz_val = vz_val or f"{w_res['Vz']:.2f}"
            pz_val = pz_val or f"{w_res['Pz']:.2f}"
        except Exception:
            pass

    vb_str = f"{vb_val} m/s [from Project Location]" if vb_val else "Not provided"
    terrain_str = str(terrain_val) if terrain_val else "Plain Terrain"
    h_str = f"{h_val} m" if h_val else "10 m"
    vz_str = f"{vz_val} m/s" if vz_val else "Not evaluated"
    pz_str = f"{pz_val} N/m\\textsuperscript{{2}}" if pz_val else "Not evaluated"

    transverse_wind_str = _render_value(input_dict, KEY_WL_TRANSVERSE_WIND_FORCE, ' kN') or "Not evaluated as lumped force (applied as grillage pressure cases per IRC 6 Cl. 209)"
    longitudinal_wind_str = _render_value(input_dict, KEY_WL_LONGITUDINAL_WIND_FORCE, ' kN') or "Not evaluated as lumped force (applied as grillage pressure cases per IRC 6 Cl. 209)"
    vertical_wind_str = _render_value(input_dict, KEY_WL_VERTICAL_WIND_FORCE, ' kN') or "Not evaluated as lumped force (applied as grillage pressure cases per IRC 6 Cl. 209)"

    # Seismic parameters (Table 3.6)
    sz_zone = weather.get("zone") or input_dict.get(KEY_SL_SEISMIC_ZONE) or "III"
    sz_z = input_dict.get(KEY_SL_ZONE_FACTOR) or weather.get("z_value") or "0.16"
    sz_i = input_dict.get(KEY_SL_IMPORTANCE_FACTOR) or "1.0"
    sz_soil = input_dict.get(KEY_SL_SOIL_TYPE) or "Type I -- Rocky or Hard"
    sz_sag = input_dict.get(KEY_SL_SPECTRAL_COEFF) or "2.8"
    sz_ah = input_dict.get(KEY_SL_HORIZONTAL_COEFF) or "0.224"
    sz_av = input_dict.get(KEY_SL_VERTICAL_COEFF) or "0.1493"

    seismic_zone_display = f"Zone {sz_zone} (Z = {sz_z}) [from Project Location]" if sz_zone and sz_z else (f"Zone {sz_zone} [from Project Location]" if sz_zone else "Not provided")
    seismic_long_force_str = "Not evaluated as lumped force (applied via response spectrum in grillage model)"
    seismic_trans_force_str = "Not evaluated as lumped force (applied via response spectrum in grillage model)"

    # Temperature parameters (Table 3.7)
    t_max_val = weather.get("max_temp") or input_dict.get(KEY_TL_HIGHEST_MAX_TEMP) or input_dict.get("shade_temp_max")
    t_min_val = weather.get("min_temp") or input_dict.get(KEY_TL_LOWEST_MIN_TEMP) or input_dict.get("shade_temp_min")

    br_min = input_dict.get(KEY_TL_BRIDGE_TEMP_MIN)
    br_max = input_dict.get(KEY_TL_BRIDGE_TEMP_MAX)
    t_rise = input_dict.get(KEY_TL_TEMP_RISE)
    t_fall = input_dict.get(KEY_TL_TEMP_FALL)

    if (not br_min or not br_max) and t_max_val is not None and t_min_val is not None:
        try:
            t_res = IRC6_2017.cl_215_2_effective_bridge_temperature(float(t_max_val), float(t_min_val), 'metallic', False)
            t_min_eff = t_res.get('T_min', 0)
            t_max_eff = t_res.get('T_max', 0)
            mean_temp = (t_max_eff + t_min_eff) / 2.0
            rise_val = t_max_eff - mean_temp
            fall_val = mean_temp - t_min_eff
            br_min = br_min or f"{t_min_eff:.2f}"
            br_max = br_max or f"{t_max_eff:.2f}"
            t_rise = t_rise or f"{rise_val:.2f}"
            t_fall = t_fall or f"{fall_val:.2f}"
        except Exception:
            pass

    t_max_str = f"{t_max_val} $^\\circ$C [from Project Location]" if t_max_val is not None else "Not provided"
    t_min_str = f"{t_min_val} $^\\circ$C [from Project Location]" if t_min_val is not None else "Not provided"
    eff_range_str = f"{br_min} to {br_max} $^\\circ$C (IRC 6 Cl. 215.2)" if (br_min and br_max) else "Not evaluated"
    rise_fall_str = f"+{t_rise} $^\\circ$C / \\textminus{{}}{t_fall} $^\\circ$C" if (t_rise and t_fall) else "Not evaluated"

    lanes = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)
    if not lanes or str(lanes).strip() in ("", "None", "0"):
        try:
            cw = float(input_dict.get(KEY_CARRIAGEWAY_WIDTH, 7.0))
            lanes_int = 2 if cw >= 5.3 else 1
        except Exception:
            lanes_int = 2
    else:
        try:
            lanes_int = int(lanes)
        except Exception:
            lanes_int = 2

    try:
        braking_force_t = IRC6_2017.cl_211_2_braking_force(lanes_int)
        braking_force_kN = braking_force_t * 9.80665
        braking_force_str = f"{braking_force_kN:.2f} kN ({braking_force_t:.2f} tonnes, {lanes_int} lanes per IRC 6 Cl. 211.2)"
    except Exception:
        braking_force_str = "Not evaluated (longitudinal braking force applied per IRC 6 Cl. 211)"

    # Centrifugal force calculation (IRC 6 Cl. 212: C = W * V^2 / (127 * R))
    radius_val = input_dict.get("geometry.radius_of_curvature") or input_dict.get("radius")
    if radius_val and float(radius_val) > 0:
        try:
            r_m = float(radius_val)
            speed_kmph = float(input_dict.get("geometry.design_speed", 80))
            centrifugal_force_str = f"Applied for R = {r_m:.1f} m, V = {speed_kmph:.0f} km/h (IRC 6 Cl. 212)"
        except Exception:
            centrifugal_force_str = "N/A (Straight Alignment)"
    else:
        centrifugal_force_str = "0.00 kN (Straight Bridge Alignment, IRC 6 Cl. 212)"

    fp_mode  = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "")
    fp_value = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE, "")
    if str(fp_mode).strip().lower() in ("as per irc 6", "as per irc6", "automatic"):
        try:
            fp_str = f"{IRC6_2017.cl_206_1_footway_load():.3f} kN/m² (IRC 6 Cl. 206.1)"
        except Exception:
            fp_str = "N/A"
    elif fp_value not in (None, ""):
        fp_str = f"{fp_value} kN/m²"
    else:
        fp_str = "N/A"

    footpath_prov = str(input_dict.get("geometry.footpath") or input_dict.get(KEY_FOOTPATH, "None")).strip()
    footpath_width = _render_value(input_dict, KEY_TS_FOOTPATH_WIDTH, " m")
    is_no_footpath = footpath_prov.lower() in ("none", "no", "", "false")

    if is_no_footpath:
        fp_prov_str = "None (Excluded from bridge layout)"
        fp_w_str = "0.0 m (No footpath)"
        fp_intensity_str = "4.905 kN/m² (IRC 6 Cl. 206.1 code provision; excluded from design — no footpath provided)"
        fp_comb_str = "Not applied (no footpath provided in bridge cross-section)"
    else:
        fp_prov_str = footpath_prov
        fp_w_str = str(footpath_width) if footpath_width else "None"
        fp_intensity_str = fp_str
        fp_comb_str = "In accordance with IRC 6 Clause 206.3"

    # Vz / Pz — prefer stored computed values; fall back to IRC6 Table 12
    vz_val = input_dict.get(KEY_WL_HOURLY_MEAN_WIND)
    pz_val = input_dict.get(KEY_WL_HOURLY_WIND_PRESSURE)
    if not vz_val or not pz_val:
        try:
            _vb  = input_dict.get(KEY_WL_BASIC_WIND_SPEED) or weather.get("wind_speed") or input_dict.get('wind_speed')
            _h   = input_dict.get(KEY_WL_AVG_EXPOSED_HEIGHT) or "10"
            _ter = {
                "Plain Terrain": "plain",
                "Terrain with Obstructions": "obstructed",
            }.get(str(input_dict.get(KEY_WL_TERRAIN_TYPE, "")).strip(), "plain")
            if _vb:
                _res = IRC6_2017.table_12(float(_h), _ter, float(_vb))
                if not vz_val:
                    vz_val = _res.get("Vz")
                if not pz_val:
                    pz_val = _res.get("Pz")
        except Exception:
            pass
    vz_str = f"{float(vz_val):.2f} m/s" if vz_val not in (None, "", "N/A") else "Not evaluated"
    pz_str = f"{float(pz_val):.2f} N/m²" if pz_val not in (None, "", "N/A") else "Not evaluated"

    # Table 3.5 — Seismic: prefer stored computed values; fall back to IRC6 cl_218_5_1
    sl_zone_factor = input_dict.get(KEY_SL_ZONE_FACTOR)
    sl_spectral    = input_dict.get(KEY_SL_SPECTRAL_COEFF)
    sl_ah          = input_dict.get(KEY_SL_HORIZONTAL_COEFF)
    sl_av          = input_dict.get(KEY_SL_VERTICAL_COEFF)
    if not sl_ah or not sl_zone_factor:
        try:
            _zone = input_dict.get(KEY_SL_SEISMIC_ZONE) or input_dict.get('seismic_zone')
            _zmap = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}
            _z    = str(_zone).strip().upper()
            if _z.isdigit():
                _z = _zmap.get(_z)
            _smap = {"Type I – Rocky or Hard": 1, "Type II – Medium Soil": 2, "Type III – Soft Soil": 3}
            _st   = _smap.get(str(input_dict.get(KEY_SL_SOIL_TYPE, "")), 1)
            _tp   = input_dict.get(KEY_SL_TIME_PERIOD)
            _damp = input_dict.get(KEY_SL_DAMPING) or "5"
            _dl_v = input_dict.get(KEY_SL_DEAD_LOAD_VALUE)
            _ll_v = input_dict.get(KEY_SL_LIVE_LOAD_VALUE)
            _dead = float(_dl_v) if str(input_dict.get(KEY_SL_DEAD_LOAD_MODE, "")) == "Custom" and _dl_v else 0.0
            _live = float(_ll_v) if str(input_dict.get(KEY_SL_LIVE_LOAD_MODE, "")) == "Custom" and _ll_v else 0.0
            _res  = IRC6_2017.cl_218_5_1(zone=f"Zone {_z}", soil_type=_st, dead_load_kN=_dead,
                        live_load_kN=_live, period_T=float(_tp) if _tp else None,
                        damping_percent=float(_damp))
            if not sl_zone_factor:
                sl_zone_factor = _res.get("Z")
            if not sl_spectral:
                sl_spectral    = _res.get("Sa_g_adjusted")
            if not sl_ah:
                sl_ah          = _res.get("Ah")
            if not sl_av:
                sl_av          = round(_res.get("Ah", 0) * 2 / 3, 4)
        except Exception:
            pass

    def _sl(v, unit=""):
        return f"{float(v):.4f}{unit}" if v not in (None, "") else "N/A"

    # Table 3.6 — Temperature: compute effective bridge temp range from shade temps
    tl_temp_min = tl_temp_max = tl_rise = tl_fall = "N/A"
    try:
        _tmax = input_dict.get(KEY_TL_HIGHEST_MAX_TEMP) or weather.get("max_temp") or input_dict.get('shade_temp_max')
        _tmin = input_dict.get(KEY_TL_LOWEST_MIN_TEMP)  or weather.get("min_temp") or input_dict.get('shade_temp_min')
        if _tmax is not None and _tmin is not None:
            _res    = IRC6_2017.cl_215_2_effective_bridge_temperature(
                          float(_tmax), float(_tmin), 'metallic', False)
            _bt_min = _res.get('T_min', 0)
            _bt_max = _res.get('T_max', 0)
            _mean   = (_bt_max + _bt_min) / 2.0
            tl_temp_min = f"{_bt_min:.2f}"
            tl_temp_max = f"{_bt_max:.2f}"
            tl_rise     = f"{_bt_max - _mean:.2f}"
            tl_fall     = f"{_mean - _bt_min:.2f}"
    except Exception:
        pass

    t_max_str = f"{t_max_val} °C [from Project Location]" if t_max_val is not None else "Not provided"
    t_min_str = f"{t_min_val} °C [from Project Location]" if t_min_val is not None else "Not provided"
    eff_range_str = f"{tl_temp_min} to {tl_temp_max} °C (IRC 6 Cl. 215.2)" if (tl_temp_min != "N/A" and tl_temp_max != "N/A") else "Not evaluated"
    rise_fall_str = f"+{tl_rise} °C / -{tl_fall} °C" if (tl_rise != "N/A" and tl_fall != "N/A") else "Not evaluated"

    # --- Table 3.7: Load Combinations (dynamically generated from IRC 6) ---
    _LOAD_LABEL_MAP = {
        'dead_load':         'DL',
        'surfacing':         'SIDL',
        'live_load':         'LL',
        'wind_load':         'WL',
        'thermal_load':      'TL',
        'vehicle_collision': 'VC',
        'barge_impact':      'BI',
        'floating_bodies':   'FB',
        'seismic':           'EQ',
    }

    def _fmt_factors(factors):
        """Format a factors dict into a compact load-case string for the table."""
        parts = []
        for load, val in factors.items():
            label = _LOAD_LABEL_MAP.get(load, load.upper())
            if isinstance(val, dict):  # permanent load with adding/relieving
                add = val.get('adding')
                rel = val.get('relieving')
                add_s = f"{add:.2f}" if add is not None else '--'
                rel_s = f"{rel:.2f}" if rel is not None else '--'
                parts.append(f"{label}({add_s}/{rel_s})")
            else:
                if val is None:
                    continue  # skip N/A factors
                parts.append(f"{label}({val:.2f})")
        return ' + '.join(parts)

    uls_combos = IRC6_2017.uls_load_combinations()
    sls_combos = IRC6_2017.sls_load_combinations()
    lc_rows = []
    for i, combo in enumerate(uls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(
            f"ULS-{i:02d}" + r" & " + cases + r" \\[6pt]" + "\n"
            + r"\hline"
        )
    for i, combo in enumerate(sls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(
            f"SLS-{i:02d}" + r" & " + cases + r" \\[6pt]" + "\n"
            + r"\hline"
        )

    lc_rows_str = "\n".join(lc_rows)

    return r"""
\chapter{Loads and Load Combinations}

This section summarizes all loads applied to the bridge and the load combinations considered for analysis and design.

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Dead Load -- Self Weight}} \\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endfirsthead
\multicolumn{2}{c}{{\bfseries Dead Load -- Self Weight (continued)}} \\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endhead
\hline
\multicolumn{2}{r}{\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
\textnormal{Steel Self-Weight Applied} & """ + (_render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, ' kN/m\\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textnormal{Concrete Deck Weight} & """ + (_render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, ' kN/m\\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textnormal{Self-Weight Factor} & """ + (_render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR)) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Dead Load for Surfacing (DW)}} \\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endfirsthead
\multicolumn{2}{c}{{\bfseries Dead Load for Surfacing (continued)}} \\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endhead
\hline
\multicolumn{2}{r}{\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
\textnormal{Wearing Course Load} & """ + (_render_value(input_dict, KEY_WC_MATERIAL)) + r""" x """ + (_render_value(input_dict, KEY_WC_THICKNESS)) + r""" \\[6pt]
\hline
\textnormal{Additional SIDL (Crash Barrier)} & """ + (_render_value(input_dict, KEY_CB_LOAD)) + r""" kN/m per barrier \\[6pt]
\hline
\textnormal{Railing Load} & """ + (_render_value(input_dict, KEY_RL_LOAD_VALUE)) + r""" kN/m\sdstar{} \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Vehicle Live Loads (LL)}} \\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endfirsthead
\multicolumn{2}{c}{{\bfseries Vehicle Live Loads (continued)}} \\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endhead
\hline
\multicolumn{2}{r}{\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
\textnormal{Vehicle Class(es) Selected} & """ + _tex(vehicles_str) + r""" \\[6pt]
\hline
\textnormal{Impact Factor (IRC 6 Cl. 208)} & """ + _tex(impact_factor_str) + r""" \\[6pt]
\hline
\textnormal{Braking Force (IRC 6 Cl. 211)} & """ + _tex(braking_force_str) + r""" \\[6pt]
\hline
\textnormal{Centrifugal Force (IRC 6 Cl. 212)} & """ + _tex(centrifugal_force_str) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Footway / Pedestrian Live Load (IRC 6 Cl. 206)}} \\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endfirsthead
\multicolumn{2}{c}{{\bfseries Footway / Pedestrian Live Load (continued)}} \\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endhead
\hline
\multicolumn{2}{r}{\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
\textnormal{Footpath Provided} & """ + _tex(fp_prov_str) + r""" \\[6pt]
\hline
\textnormal{Footpath Width} & """ + _tex(fp_w_str) + r""" \\[6pt]
\hline
\textnormal{Pedestrian Live Load Intensity} & """ + _tex(fp_intensity_str) + r""" \\[6pt]
\hline
\textnormal{Combination with Live Load} & """ + _tex(fp_comb_str) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Wind Load (WL) --- per IRC 6}} \\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endfirsthead
\multicolumn{2}{c}{{\bfseries Wind Load (continued)}} \\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endhead
\hline
\multicolumn{2}{r}{\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
\textnormal{Basic Wind Speed, Vb} & """ + _tex(vb_str) + r""" \\[6pt]
\hline
\textnormal{Terrain Type} & """ + _tex(terrain_str) + r""" \\[6pt]
\hline
\textnormal{Average Exposed Height, H (m)} & """ + _tex(h_str) + r""" \\[6pt]
\hline
\textnormal{Hourly Mean Wind Speed, Vz} & """ + _tex(vz_str) + r""" \\[6pt]
\hline
\textnormal{Hourly Wind Pressure, Pz} & """ + _tex(pz_str) + r""" \\[6pt]
\hline
\textnormal{Transverse Wind Force} & """ + _tex(transverse_wind_str) + r""" \\[6pt]
\hline
\textnormal{Longitudinal Wind Force} & """ + _tex(longitudinal_wind_str) + r""" \\[6pt]
\hline
\textnormal{Vertical Wind Force} & """ + _tex(vertical_wind_str) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Earthquake Load (EL) --- per IRC 6}} \\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endfirsthead
\multicolumn{2}{c}{{\bfseries Earthquake Load (continued)}} \\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endhead
\hline
\multicolumn{2}{r}{\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
\textnormal{Seismic Zone} & """ + _tex(seismic_zone_display) + r""" \\[6pt]
\hline
\textnormal{Zone Factor, Z} & """ + _tex(str(sz_z)) + r""" \\[6pt]
\hline
\textnormal{Importance Factor, I} & """ + _tex(str(sz_i)) + r""" \\[6pt]
\hline
\textnormal{Type of Soil} & """ + _tex(str(sz_soil)) + r""" \\[6pt]
\hline
\textnormal{Sa/g} & """ + _tex(str(sz_sag)) + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Coefficient, Ah} & """ + _tex(str(sz_ah)) + r""" \\[6pt]
\hline
\textnormal{Vertical Seismic Coefficient, Av} & """ + _tex(str(sz_av)) + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Force (longitudinal)} & """ + _tex(seismic_long_force_str) + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Force (transverse)} & """ + _tex(seismic_trans_force_str) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Temperature Load (TL) --- per IRC 6}} \\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endfirsthead
\multicolumn{2}{c}{{\bfseries Temperature Load (continued)}} \\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endhead
\hline
\multicolumn{2}{r}{\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
\textnormal{Maximum Shade Temperature} & """ + _tex(t_max_str) + r""" \\[6pt]
\hline
\textnormal{Minimum Shade Temperature} & """ + _tex(t_min_str) + r""" \\[6pt]
\hline
\textnormal{Effective Bridge Temp. Range} & """ + _tex(eff_range_str) + r""" \\[6pt]
\hline
\textnormal{Temperature Rise / Fall for Design} & """ + _tex(rise_fall_str) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|C{4.0cm}|p{11.5cm}|}
\caption{\textbf{Load Combinations}} \\
\hline
\textbf{Combination ID} & \textbf{Load Cases} \\[6pt]
\hline
\endfirsthead
\multicolumn{2}{c}{{\bfseries Load Combinations (continued)}} \\
\hline
\textbf{Combination ID} & \textbf{Load Cases} \\[6pt]
\hline
\endhead
\hline
\multicolumn{2}{r}{\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
""" + lc_rows_str + r"""
\end{longtable}

\noindent\textit{Note: All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.}
"""


