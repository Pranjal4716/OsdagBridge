
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _get_number(value):
    """Convert a numeric/BOQ value into a float, ignoring unavailable values."""
    try:
        if value is None or str(value).strip().upper() in ("N.A.", "NA", "", "---", "NONE"):
            return None
        number = float(value)
        if number < 0:
            return None
        return number
    except (TypeError, ValueError):
        return None


def _create_horizontal_ur_chart(labels, ur_values, title, output_path):
    """
    Helper to generate a standardized horizontal bar chart for Utilization Ratios (UR).
    - Threshold at UR = 1.0 (red dashed line).
    - Color: Forest Green (#2E7D32) if <= 1.0, Crimson Red (#C62828) if > 1.0.
    - Value labels on each bar.
    """
    if not labels or not ur_values:
        return None

    fig, ax = plt.subplots(figsize=(8.5, max(3.5, len(labels) * 0.45 + 1.2)))

    # Invert so first item appears at the top
    y_pos = list(range(len(labels)))
    y_pos.reverse()

    colors = ["#2E7D32" if val <= 1.0 else "#C62828" for val in ur_values]

    bars = ax.barh(y_pos, ur_values, height=0.55, color=colors, edgecolor="#333333", linewidth=0.6, zorder=3)

    # Threshold line at UR = 1.0
    ax.axvline(1.0, color="#D32F2F", linestyle="--", linewidth=1.8, label="Code Limit (UR = 1.0)", zorder=4)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel("Utilization Ratio (UR = Demand / Capacity)", fontsize=10, fontweight="bold")
    ax.set_title(title, fontsize=12, fontweight="bold", pad=12)

    # Upper limit for x-axis
    max_val = max(ur_values)
    x_max = max(1.2, max_val * 1.15)
    ax.set_xlim(0, x_max)

    # Gridlines and styling
    ax.grid(axis="x", linestyle=":", alpha=0.6, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", fontsize=9, framealpha=0.9)

    # Add numeric labels at the end of each bar
    for bar, val in zip(bars, ur_values):
        ax.text(
            bar.get_width() + 0.02,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.2f}",
            va="center",
            ha="left",
            fontsize=9,
            fontweight="bold",
            color="#222222"
        )

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


def generate_ur_charts(bridge, output_dir):
    """
    Generate Utilization Ratio (UR = Demand / Capacity) charts for Chapter 5:
    1. Steel Plate Girders
    2. Concrete Deck Slab
    3. Cross Bracing
    4. End Diaphragms

    Returns:
        Dictionary mapping chart keys to their generated PNG file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    chart_paths = {
        "ur_plate_girders": None,
        "ur_deck_slab": None,
        "ur_cross_bracing": None,
        "ur_end_diaphragm": None,
    }

    out = getattr(bridge, "output_dict", {}) or {}
    inp = getattr(bridge, "input_dict", {}) or {}

    # -------------------------------------------------------------------------
    # 1. Steel Plate Girders UR Chart
    # -------------------------------------------------------------------------
    dr = out.get("design_results", {}) or {}
    cat_urs = dr.get("category_urs", {}) or {}

    girder_labels = []
    girder_urs = []

    if cat_urs:
        # Sort by category_no
        for _, cdata in sorted(cat_urs.items()):
            lbl = cdata.get("label", "")
            dcr = _get_number(cdata.get("max_dcr"))
            if dcr is not None:
                girder_labels.append(lbl)
                girder_urs.append(dcr)
    else:
        # Fallback to direct output keys
        checks = [
            ("Strength – Flexure", out.get("util.flexure")),
            ("Strength – Shear", out.get("util.shear")),
            ("Lateral Torsional Buckling", out.get("util.ltb")),
            ("Interaction (M-V)", out.get("util.interaction")),
        ]
        for lbl, val in checks:
            dcr = _get_number(val)
            if dcr is not None:
                girder_labels.append(lbl)
                girder_urs.append(dcr)

    if girder_labels and girder_urs:
        p = os.path.join(output_dir, "ur_plate_girders.png")
        chart_paths["ur_plate_girders"] = _create_horizontal_ur_chart(
            girder_labels, girder_urs, "Steel Plate Girders — Utilization Ratios", p
        )

    # -------------------------------------------------------------------------
    # 2. Concrete Deck Slab UR Chart
    # -------------------------------------------------------------------------
    from osdagbridge.core.utils.common import (
        KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT,
        KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP,
        KEY_DD_M_ULS_OH, KEY_DD_MU_OH,
        KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA,
        KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC,
        KEY_DD_WK_BOT, KEY_DD_WK_TOP, KEY_DD_WK_OH, KEY_DD_WK_LIMIT,
        KEY_DD_HAS_OVERHANG
    )
    deck_rpt = out.get("deck_report_values", {}) or {}

    deck_checks = [
        ("Flexure – Interior Sagging", KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT),
        ("Flexure – Interior Hogging", KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP),
    ]
    if deck_rpt.get(KEY_DD_HAS_OVERHANG, True):
        deck_checks.append(("Flexure – Cantilever Overhang", KEY_DD_M_ULS_OH, KEY_DD_MU_OH))

    deck_checks.extend([
        ("Punching Shear (Cl. 10.4.6)", KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA),
        ("One-Way Beam Shear", KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC),
    ])

    deck_labels = []
    deck_urs = []

    for label, dem_k, cap_k in deck_checks:
        dem = _get_number(deck_rpt.get(dem_k))
        cap = _get_number(deck_rpt.get(cap_k))
        if dem is not None and cap is not None and cap > 0:
            ur = dem / cap
            deck_labels.append(label)
            deck_urs.append(ur)

    # Crack width check
    wk_lim = _get_number(deck_rpt.get(KEY_DD_WK_LIMIT))
    wk_vals = [
        _get_number(deck_rpt.get(k))
        for k in (KEY_DD_WK_BOT, KEY_DD_WK_TOP, KEY_DD_WK_OH)
    ]
    wk_max = max((v for v in wk_vals if v is not None), default=None)
    if wk_max is not None and wk_lim is not None and wk_lim > 0:
        deck_labels.append("Crack Width Check")
        deck_urs.append(wk_max / wk_lim)

    if deck_labels and deck_urs:
        p = os.path.join(output_dir, "ur_deck_slab.png")
        chart_paths["ur_deck_slab"] = _create_horizontal_ur_chart(
            deck_labels, deck_urs, "Concrete Deck Slab — Utilization Ratios", p
        )

    # -------------------------------------------------------------------------
    # 3. Cross Bracing UR Chart
    # -------------------------------------------------------------------------
    cb_labels = []
    cb_urs = []

    cb_pairs = []
    if hasattr(bridge, "get_cb_pairs"):
        cb_pairs = bridge.get_cb_pairs()

    if cb_pairs:
        for pair in cb_pairs:
            for member in ("diagonal", "chord"):
                for force_type in ("compression", "tension"):
                    eff = None
                    if hasattr(bridge, "get_cb_efficiency"):
                        eff = _get_number(bridge.get_cb_efficiency(pair, member, force_type))
                    if eff is not None:
                        m_lbl = "Diag" if member == "diagonal" else "Chord"
                        f_lbl = "Comp" if force_type == "compression" else "Tens"
                        cb_labels.append(f"{pair} {m_lbl} ({f_lbl})")
                        cb_urs.append(eff)

        # Cross bracing slenderness
        for pair in cb_pairs:
            for member in ("diagonal", "chord"):
                if hasattr(bridge, "get_cb_slenderness"):
                    s = _get_number(bridge.get_cb_slenderness(pair, member))
                    if s is not None:
                        lim = 400.0 if member == "chord" else 250.0
                        m_lbl = "Diag" if member == "diagonal" else "Chord"
                        cb_labels.append(f"{pair} {m_lbl} Slenderness")
                        cb_urs.append(s / lim)

    if cb_labels and cb_urs:
        p = os.path.join(output_dir, "ur_cross_bracing.png")
        chart_paths["ur_cross_bracing"] = _create_horizontal_ur_chart(
            cb_labels, cb_urs, "Cross Bracing Members — Utilization Ratios", p
        )

    # -------------------------------------------------------------------------
    # 4. End Diaphragm UR Chart
    # -------------------------------------------------------------------------
    ed_labels = []
    ed_urs = []

    # If configured as cross bracing, use diaphragm design results only if genuinely calculated
    ed_pairs_data = out.get("end_diaphragm_design_results", {}) or {}
    if ed_pairs_data and any(ed_pairs_data.values()):
        for pair, pdata in ed_pairs_data.items():
            for member in ("diagonal", "chord", "top_chord", "bottom_chord"):
                mdata = pdata.get(member, {}) if isinstance(pdata, dict) else {}
                for ft in ("compression", "tension"):
                    rdata = mdata.get(ft, {}) if isinstance(mdata, dict) else {}
                    eff = _get_number(rdata.get("efficiency"))
                    if eff is not None:
                        m_lbl = member.replace("_", " ").title()
                        f_lbl = "Comp" if ft == "compression" else "Tens"
                        ed_labels.append(f"{pair} {m_lbl} ({f_lbl})")
                        ed_urs.append(eff)

    if ed_labels and ed_urs:
        p = os.path.join(output_dir, "ur_end_diaphragm.png")
        chart_paths["ur_end_diaphragm"] = _create_horizontal_ur_chart(
            ed_labels, ed_urs, "End Diaphragm Members — Utilization Ratios", p
        )

    return chart_paths


def generate_material_charts(quantities, output_dir):
    """
    Generate material quantity charts for Chapter 7:
    - Chart 7.1: Structural Steel Quantities (Girders, Top Bracing, Bottom Bracing, Diagonal Bracing, Shear Studs, Crash Barrier)
    - Chart 7.2: Concrete and Reinforcement Quantities

    Returns:
        Dictionary containing generated chart image paths.
    """
    os.makedirs(output_dir, exist_ok=True)

    chart_paths = {
        "structural_steel": None,
        "concrete_reinforcement": None,
    }

    # --------------------------------------------------
    # Chart 7.1: Structural Steel Quantities
    # --------------------------------------------------
    steel_items = {
        "Steel Girders": "steel_girders_wt_total",
        "Top Bracing": "bracing_top_wt_total",
        "Bottom Bracing": "bracing_bot_wt_total",
        "Diagonal Bracing": "bracing_diag_wt_total",
        "Shear Studs": "shear_studs_wt_total",
    }

    steel_labels = []
    steel_values = []

    for label, key in steel_items.items():
        value = _get_number(quantities.get(key))
        if value is not None and value > 0:
            steel_labels.append(label)
            steel_values.append(value)

    if steel_values:
        fig, ax = plt.subplots(figsize=(9, 5))

        bars = ax.bar(
            steel_labels,
            steel_values,
            width=0.55,
            color="#1F77B4",
            edgecolor="#114B72",
            linewidth=0.8,
            zorder=3
        )

        ax.set_title("Structural Steel Quantities", fontsize=13, fontweight="bold", pad=12)
        ax.set_ylabel("Weight (Metric Tonnes, MT)", fontsize=10, fontweight="bold")
        ax.set_xlabel("Structural Steel Components", fontsize=10, fontweight="bold")
        ax.grid(axis="y", linestyle="--", alpha=0.5, zorder=0)
        ax.set_axisbelow(True)

        ax.bar_label(bars, fmt="%.2f MT", padding=3, fontsize=9, fontweight="bold")
        ax.tick_params(axis="x", rotation=15)
        fig.tight_layout()

        path = os.path.join(output_dir, "structural_steel_quantities.png")
        fig.savefig(path, dpi=300, bbox_inches="tight")
        plt.close(fig)

        chart_paths["structural_steel"] = path

    # --------------------------------------------------
    # Chart 7.2: Concrete and Reinforcement Quantities
    # --------------------------------------------------
    concrete_deck_vol = _get_number(quantities.get("concrete_deck_vol_total"))
    crash_barrier_vol = _get_number(quantities.get("crash_barrier_vol_total"))
    reinforcement_weight = _get_number(quantities.get("rebar_deck_wt_total"))

    conc_labels = []
    conc_vols = []
    if concrete_deck_vol is not None and concrete_deck_vol > 0:
        conc_labels.append("Deck Slab")
        conc_vols.append(concrete_deck_vol)
    if crash_barrier_vol is not None and crash_barrier_vol > 0:
        conc_labels.append("Crash Barrier")
        conc_vols.append(crash_barrier_vol)

    if conc_vols or reinforcement_weight is not None:
        fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.5))

        if conc_vols:
            bars0 = axes[0].bar(conc_labels, conc_vols, width=0.45, color=["#7F7F7F", "#A0A0A0"][:len(conc_labels)], edgecolor="#4F4F4F", linewidth=0.8, zorder=3)
            axes[0].bar_label(bars0, fmt="%.2f m³", padding=3, fontsize=9, fontweight="bold")
            axes[0].set_title("Concrete Volumes", fontsize=11, fontweight="bold")
            axes[0].set_ylabel("Volume (m³)", fontsize=10, fontweight="bold")
            axes[0].grid(axis="y", linestyle="--", alpha=0.5, zorder=0)
            axes[0].set_axisbelow(True)
            axes[0].set_ylim(0, max(conc_vols) * 1.25)
        else:
            axes[0].set_visible(False)

        if reinforcement_weight is not None:
            bars1 = axes[1].bar(["Deck Rebar"], [reinforcement_weight], width=0.45, color="#D62728", edgecolor="#8B0000", linewidth=0.8, zorder=3)
            axes[1].bar_label(bars1, fmt="%.2f MT", padding=3, fontsize=9, fontweight="bold")
            axes[1].set_title("Reinforcement Steel Weight", fontsize=11, fontweight="bold")
            axes[1].set_ylabel("Weight (Metric Tonnes, MT)", fontsize=10, fontweight="bold")
            axes[1].grid(axis="y", linestyle="--", alpha=0.5, zorder=0)
            axes[1].set_axisbelow(True)
            axes[1].set_ylim(0, reinforcement_weight * 1.25)
        else:
            axes[1].set_visible(False)

        fig.suptitle("Concrete Volumes and Reinforcement Quantities", fontsize=13, fontweight="bold")
        fig.tight_layout()

        path = os.path.join(output_dir, "concrete_reinforcement_quantities.png")
        fig.savefig(path, dpi=300, bbox_inches="tight")
        plt.close(fig)

        chart_paths["concrete_reinforcement"] = path

    return chart_paths

