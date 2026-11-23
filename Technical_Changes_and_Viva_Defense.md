# FOSSEE Project 1 — LaTeX Report Generator Refactoring & Enhancements
## Technical Implementation, Verification & Viva Defense Guide

**Project:** OsdagBridge (FOSSEE Project 1)  
**Deliverables:**
- `Report_Before.pdf` (Baseline report: empty inputs, placeholder dashes, unstyled)
- `Report_After.pdf` (Enhanced report: 66 total pages [1 unnumbered cover + 65 numbered pages], 1.46 MB, full inputs, multi-page tables, UR & material charts, 17 CAD/drawing/envelope figures, zero placeholders)
- `Technical_Changes_and_Viva_Defense.md` (Complete technical change documentation and defense notes)

---

## 1. Executive Summary of Achievements

| Requirement | Baseline State (Before) | Refactored State (After) | Status |
| :--- | :--- | :--- | :---: |
| **Input Data Pipeline** | Report showed `None` / empty dictionaries; 0 keys loaded | Fixed UI/Backend synchronization; 580 input keys & 1,070 output keys reliably extracted | **VERIFIED** |
| **Page Numbering Consistency** | Cover and TOC both showed "Page 1 of 63"; LastPage mismatch | Cover page unnumbered (`\thispagestyle{empty}`); TOC starts as Page 1 of 65; all 65 content pages numbered consistently `Page X of 65` | **VERIFIED** |
| **Multi-Page Tables & Formatting** | Headers lost across page breaks; broken captions (`! Misplaced \noalign`) | Standardized `longtable` across Ch. 2, 3, 4, 5, 7 with `\caption{...} \\`, `\endfirsthead`, `\endhead`, `\endfoot`, `\endlastfoot`; `\needspace` guards prevent orphaned headers | **VERIFIED** |
| **Report Layout & Typography** | Inconsistent margins, footer overlaps, unescaped unicode glyphs crashing `pdflatex` | Centralized `styles.py`, `GEOMETRY_OPTIONS` (`footskip=28pt`), native `\DeclareUnicodeCharacter`, custom wrapped column types | **VERIFIED** |
| **Chapter 3 (Loads)** | Combined live load & footway; missing dynamic impact & braking forces | Distinct tables for Vehicle Live Load (Table 3.3) and Footway Load (Table 3.4); full IRC 6 dynamic and braking metrics | **VERIFIED** |
| **Chapter 4 (Envelopes & Reactions)** | Placeholders on Page 19; empty reaction rows | Real Bending Moment Envelope (Envelope ULS), Shear Force Envelope, and Vertical Deflection ($D_y$) captured and embedded; Table 4.2 Reactions populated | **VERIFIED** |
| **Chapter 5 (Cross Bracing Design)** | Missing section properties for cross-bracing; ambiguous shear terminology; missing charts | 3 Horizontal UR charts with dashed limit threshold at UR = 1.0; equal angle properties ($A_g = 237\text{ mm}^2, r_{min} = 8\text{ mm}$) populated; longitudinal interface shear clarified ($V_L = 76.27\text{ kN/m}$ vs $V_{Rd} = 999.28\text{ kN/m}$, UR = 0.08 PASS) | **VERIFIED** |
| **Chapter 5 (End Diaphragm Checks)** | Previously mirrored Cross Bracing values into End Diaphragm | Rigorous solver audit: grillage resolves support lateral forces at bearings and does not compute member internal forces; Table 5.28 & 5.29 explicitly state "Unavailable / Not Evaluated" with engineering note (no fabricated PASS) | **VERIFIED** |
| **Chapter 6 (Drawings & CAD)** | Empty placeholders for CAD diagrams | 14 CAD diagrams captured from 3D renderer and preview widgets, embedded and scaled | **VERIFIED** |
| **Chapter 7 (Material Take-off & BOQ)** | Placeholder/dummy quantities; N.A. for bracings | Complete deterministic BOQ from actual layout: Girders (32.89 MT), Top Chord (0.10 MT), Bottom Chord (0.10 MT), Diagonal (0.24 MT), Concrete Deck (59.25 m³, 148.12 MT), Rebar (2.90 MT), Crash Barrier (45.34 MT), Shear Studs (608 connectors, 0.02 m³, 0.150 MT) | **VERIFIED** |
| **Executive Summary Status** | Contradiction: Overall FAIL vs "Girder design pass" | Reconciled: Clearly explains that static ULS bending and shear resistance pass, while governing status is FAIL due to Fatigue normal stress range per IRC 22:2015 Cl. 605.3 | **VERIFIED** |
| **LaTeX Compilation** | Fatal errors, 260+ syntax crashes | Return Code: 0, 100% clean compilation to 66-page PDF (1.46 MB) with zero placeholders | **VERIFIED** |

---

## 2. Detailed Technical Problem-Solution Breakdown

### 2.1 Critical Bug: Report Input Pipeline ("Total input keys: 0")
- **Original Problem:** When generating reports, terminal diagnostics reported `Total input keys: 0`, and the generated PDF showed empty tables and dashed placeholders despite `inputs.osi` being loaded.
- **Root Cause Analysis:** In `template_page.py`, `CustomWindow` maintained an internal `self.input_dict`, but `self.backend.set_input()` was only triggered when the user clicked the "Design" button. If the user loaded an `.osi` file and pressed "Create Design Report" (Alt+C) before or without a synchronized run, the backend dictionary remained completely empty.
- **Implementation:**
  1. Synchronized `loadOSI_inputs()` in `template_page.py` so loaded YAML inputs are immediately pushed to `self.backend.set_input(self.input_dict)`.
  2. Implemented execution validation guards in `open_report_dialog()` and `output_dock.py`: report generation is blocked with an informative user warning (`"Please run the design first."`) if `backend.output_dict` is empty.
  3. Added null-safe fallback handling in `report_generator.py` for `figure_data` so direct programmatic and UI calls succeed seamlessly.

---

### 2.2 Page Numbering Consistency Fix
- **Original Problem:** Both the Cover page and the Table of Contents displayed `Page 1 of 63`, creating an off-by-one discrepancy across the entire document footer.
- **Root Cause Analysis:** `title_page()` in `report_generator.py` used `\thispagestyle{firstpage}`, where `firstpage` had `\fancyfoot[R]{Page \thepage\ of \pageref{LastPage}}`. When `\begin{titlepage}` executed, LaTeX set `\thepage = 1`, printing `Page 1 of 63` on the cover. Upon `\end{titlepage}`, LaTeX automatically resets `\setcounter{page}{1}`, causing the TOC page to also be numbered `Page 1 of 63`.
- **Implementation:**
  1. Set `\thispagestyle{empty}` on `\begin{titlepage}` so the cover page has no header, footer, or page number.
  2. Redefined `\fancypagestyle{firstpage}` with empty header and footer.
  3. The Table of Contents starts cleanly as `Page 1 of 65`, Executive Summary is `Page 2 of 65`, and References ends at `Page 65 of 65`.
  4. Total PDF page count is 66 (1 unnumbered cover + 65 numbered content pages).

---

### 2.3 End Diaphragm Solver Verification & Elimination of Fabricated Data
- **Original Problem:** End Diaphragm Table 5.28 and Table 5.29 displayed identical values to Cross Bracing Table 5.25 (e.g. Demand 7.735 kN, Capacity 17.910 kN, UR 0.710, PASS), risking technical invalidity if unsupported by the solver.
- **Root Cause Analysis:** Inspection of `PlateGirderBridge._design_end_diaphragm_members()` revealed that `end_diaphragm_forces_dict["pairs"]` contains `None` for all internal member forces because the grillage analysis resolves transverse reactions directly at support bearing nodes. Previous report code had copied `cb_capacity_content` into Table 5.28 and Table 5.29.
- **Implementation:**
  1. **Table 5.26 (Connection & Section Properties):** Retained genuine input/database properties for the configured framing (ISA $40 \times 40 \times 3$, $A_g = 237.0\text{ mm}^2, r_{min} = 8.0\text{ mm}$, Bolted).
  2. **Table 5.27 (Slenderness Check):** Retained geometric slenderness calculation ($KL = 2432\text{ mm}, KL/r = 128.5 \le 250$ PASS).
  3. **Table 5.28 (Capacity Summary):** Do not copy Cross Bracing values. All member rows explicitly display:
     `Governing LC: ---`, `Demand: Unavailable`, `Capacity: Unavailable`, `UR: ---`, `Status: Not Evaluated`.
     Footnote: *"End diaphragm framing is configured with ISA 40 × 40 × 3 bracing at support locations. In the current grillage analysis implementation, transverse bearing reactions are resolved directly at the support nodes; individual member axial forces, capacity, and utilization ratios for end diaphragms were not evaluated by the solver in this version."*
  4. **Table 5.29 (Overall Summary):** End Diaphragm rows display `Unavailable` rather than implying PASS.
  5. **Report Charts:** Removed artificial fallback mirroring in `report_charts.py` so fabricated UR bars are never generated.

---

### 2.4 Multi-Page LongTable Header, Footer & Page Break Standardization
- **Original Problem:** Awkward table breaks and repeated continuation captions in Chapter 5 (Tables 5.22 to 5.28), with Table 5.29 splitting awkwardly across pages.
- **Implementation:**
  1. Added `\clearpage` before Section 5.3 (Cross Bracing Design), Section 5.4 (End Diaphragm Design), and Section 5.5 (Overall Design Check Summary).
  2. Inserted `\needspace{7\baselineskip}` before sub-tables 5.24, 5.25, 5.27, and 5.28 to guarantee tables never start unless sufficient vertical space exists, eliminating orphaned headers and unwanted continuation lines.
  3. Table 5.29 now begins at the top of page 50 and stays contiguous on a single page.

---

### 2.5 Chapter 4: Analysis Envelope Visualizations & Reactions
- **Original Problem:** Page 19 displayed empty placeholder boxes for Bending Moment Envelope and Vertical Deflection, and Table 4.2 had hardcoded empty reaction rows.
- **Implementation:**
  - Integrated `capture_report_figures()` in `output_dock.py` and report generation scripts to extract `bm_envelope` (Mz, Envelope ULS), `sf_envelope` (Fy, Envelope ULS), and `defl_ll` (Dy, 1.0 LL) as high-res PNG bytes directly from OpenSees grillage results.
  - Dynamically populated Table 4.2 ("Reactions at Supports") from the load case reaction dictionary (`rxn_summary`).

---

### 2.6 Chapter 5: Design Checks, Section Properties & Shear Terminology
- **Original Problem:** Ambiguous shear terminology (longitudinal interface shear vs transverse slab shear).
- **Implementation:**
  - Added `_lookup_angle_props()` to query `Intg_osdag.sqlite` for equal angles (e.g., `∠ 40 x 40 x 3` $\rightarrow A_g = 237.0\text{ mm}^2, r_v = 8.0\text{ mm}$).
  - Clarified shear check terminology in Table 5.15 and Table 5.29: Applied load is *Longitudinal Shear at interface per unit length* ($V_L = 76.27\text{ kN/m}$ per IRC 22 Cl. 606.10), resisted by *Transverse Shear Capacity of concrete slab / flange* ($V_{Rd} = 999.28\text{ kN/m}$ per IRC 22 Cl. 606.10.4), resulting in $\text{UR} = 0.08$ (PASS).
  - Generated component Utilization Ratio charts with red dashed threshold line at $\text{UR} = 1.0$.

---

### 2.7 Chapter 7: Bill of Materials & Shear Stud Quantification
- **Original Problem:** Clarification needed on Shear Stud connector count (608 in PDF vs 1,812 in previous chat comment).
- **Mathematical & Code Verification:**
  - Span $L = 30\text{ m} = 30{,}000\text{ mm}$.
  - Longitudinal stud pitch $s = 395\text{ mm}$ (from `steeldesign.details.shear.longitudinal_spacing`).
  - Connector pitch rows along bridge: $\text{int}(30{,}000 / 395) + 1 = 76$ rows.
  - Studs per row: 2 studs/row $\times 4\text{ girders} = 8$ studs per pitch position.
  - Total shear studs: $76 \times 8 = \mathbf{608\text{ connectors}}$.
  - Volume per stud ($\phi 20\text{ mm}, h = 100\text{ mm}$): $\frac{\pi}{4}(0.020)^2 \times 0.100 = 0.0000314\text{ m}^3$.
  - Total volume: $608 \times 0.0000314 = 0.0191\text{ m}^3 \approx 0.02\text{ m}^3$.
  - Total weight: $0.0191 \times 7.85\text{ tonnes/m}^3 = \mathbf{0.150\text{ MT}}$.
  - **Conclusion:** The PDF and `boq_generator.py` correctly reported 608 connectors. The number 1,812 was an erroneous manual note in an earlier chat comment.

---

### 2.8 Executive Summary Reconciliation
- **Original Problem:** Discrepancy where Table 1 / Project Overview indicated Overall Status `Fail (Fatigue Normal Stress, Intermediate Stiffeners)` while Key Outcomes Summary stated `Girder design pass`.
- **Implementation:**
  - Reconciled outcomes in `executive_summary.py`: Clearly documents that static strength checks for plate girders (ULS flexure and shear resistance) satisfy code requirements with low utilization ($\text{UR} < 0.35$), while the governing status is FAIL due to Serviceability / Fatigue normal stress range ($\Delta\sigma = 32.32\text{ MPa}$, $\text{UR} = 1.53 > 1.0$ per IRC 22:2015 Cl. 605.3).

---

### 2.9 Final Targeted Audit: Section Consistency, Environmental Parameters & Charts
- **Section Size Consistency (Ch. 2 vs Ch. 5):**
  - *Tracing & Source Analysis:* Traced `inputs.osi` user trials which specified `IS 100 x 100 x 10` for both Cross Bracing and End Diaphragms. During analysis, Osdag member design module optimized the Cross Bracing to `40 x 40 x 3` (single angle ISA) based on small design axial forces (7.74 kN compression, 7.42 kN tension). For End Diaphragms, however, the solver did not run member optimization, retaining the user-specified section `IS 100 x 100 x 10`.
  - *Resolution:* Added an explicit explanatory note under Cross Bracing Table 5.23 clarifying that the trial section `IS 100 x 100 x 10` from Chapter 2 was optimized to `40 x 40 x 3`. For End Diaphragms (Tables 5.26, 5.27, and 5.28), corrected member properties to reflect the genuine `IS 100 x 100 x 10` section ($A_g = 1910.0\text{ mm}^2, r_{min} = 19.7\text{ mm}$, $KL = 2432\text{ mm}, KL/r = 123.5 \le 250$ PASS) instead of erroneously copying cross-bracing values.
- **Environmental & Load Values Pipeline (Ch. 2 & Ch. 3):**
  - Fixed dictionary extraction to retrieve weather data nested in `project.location['weather_data']` (`latitude: 18.5204`, `longitude: 73.8567`, `wind_speed: 39 m/s`, `max_temp: 43.3 °C`, `min_temp: 1.7 °C`, `zone: III`).
  - Populated Table 2.1 cleanly with `18.5204° N, 73.8567° E`, `Zone III (Z = 0.16)`, `39 m/s`, `43.3 °C / 1.7 °C`. Populated Table 2.4 traffic lanes to `2` per IRC 5 Cl. 104.3.1.
  - In Table 3.5 (Wind Load), dynamically evaluated hourly mean wind speed $V_z = 32.85\text{ m/s}$ and hourly wind pressure $P_z = 647.65\text{ N/m}^2$ using IRC 6:2017 Table 12. Explicitly noted unaggregated resultant forces as *"Not evaluated as lumped force (applied as grillage pressure cases per IRC 6 Cl. 209)"*.
  - In Table 3.6 (Earthquake Load), populated $Z = 0.16$, $I = 1.0$, $S_a/g = 2.8$, $A_h = 0.224$, $A_v = 0.1493$, and noted unaggregated forces as *"Not evaluated as lumped force (applied via response spectrum in grillage model)"*.
  - In Table 3.7 (Temperature Load), evaluated effective bridge temperature range $-8.30\text{ °C to }58.30\text{ °C}$ and design rise/fall $+33.30\text{ °C} / -33.30\text{ °C}$ per IRC 6 Cl. 215.2.
- **Material Chart Classification (Ch. 7):**
  - In `report_charts.py`, removed RCC Crash Barrier from Figure 7.1 ("Structural Steel Quantities") so it exclusively reflects structural steel elements (Girders, Top Bracing, Bottom Bracing, Diagonal Bracing, 608 Shear Studs at 0.150 MT).
  - Plotted Concrete Volumes (Deck Slab 59.25 m³, Crash Barrier 18.14 m³) alongside Reinforcement Steel (2.90 MT) in Figure 7.2.
- **Executive Summary Alignment:**
  - Replaced hardcoded "PASS" for End Diaphragm with `NOT EVALUATED (support reactions resolved at bearings; member forces not evaluated)` to guarantee 100% internal consistency across Executive Summary, detailed checks, and overall summary tables.

---

### 2.10 Final Two Audit Refinements: Braking Force & Table 5.28 Column Separation
- **Braking Force Calculation (IRC 6 Cl. 211):**
  - *Tracing & Bug Fix:* Traced `IRC6_2017.cl_211_2_braking_force(design_lanes)`. For $\le 2$ lanes, `braking_force_2` was uninitialized, triggering `UnboundLocalError`, which silently fell back to `"N/A"`. Furthermore, Class A vehicle axle loads are stored internally in Newtons ($543{,}474\text{ N} = 543.474\text{ kN} = 55.4\text{ tonnes}$).
  - *Resolution:* Fixed variable scoping and unit conversion in `irc6_2017.py`. For a 2-lane highway bridge ($CW = 7.0\text{ m}$ per IRC 5 Cl. 104.3.1), the longitudinal braking force is $20\% \times 55.419\text{ tonnes} = 11.08\text{ tonnes} = \mathbf{108.70\text{ kN}}$. Table 3.3 now cleanly reports `108.70 kN (11.08 tonnes, 2 lanes per IRC 6 Cl. 211.2)`.
- **Table 5.28 Demand/Capacity Column Formatting:**
  - *Root Cause Analysis:* The previous column specification allotted only $1.8\text{ cm}$ each for Demand and Capacity while reserving $3.0\text{ cm}$ for Governing LC (`---`). The 11-character string `"Unavailable"` exceeded $1.8\text{ cm}$, causing glyph bounding boxes to touch across the rule and extract as `"UnavailableUnavailable"`.
  - *Resolution:* Reallocated column widths in `chap5.py` to `|C{1.8cm}|L{1.8cm}|C{2.4cm}|C{1.8cm}|C{2.4cm}|C{2.4cm}|C{1.2cm}|C{2.0cm}|`, giving $2.4\text{ cm}$ each to Demand and Capacity with wrapped designation `\makecell{IS 100 $\times$ 100\\$\times$ 10}` and status `\makecell{Not\\Evaluated}`. Demand and Capacity are now cleanly separated into distinct, well-aligned columns.

---

### 2.11 Final Submission Pass: Traffic Lanes, Footpath Load Exclusion & IRC Editions Harmonization
- **Traffic Lane Count (Table 2.4):**
  - *Tracing & Resolution:* Table 2.4 previously had a blank traffic lane count because `typical_section.lane_details.lane_table_count` was omitted from `inputs.osi`. In accordance with IRC 5:2015 Cl. 104.3.1, a carriageway width of $7.0\text{ m} \ge 5.3\text{ m}$ constitutes a standard two-lane bridge. Added dynamic fallback logic in `chap2.py` so Table 2.4 explicitly outputs `2 (per IRC 5 Cl. 104.3.1)`, in complete agreement with the 2-lane braking force calculation in Table 3.3.
- **Footpath Load Exclusion Clarity (Tables 2.4 & 3.4):**
  - *Tracing & Model Verification:* Traced `analyser.py:607` (`warnings.warn("No footpath component in layout; skipping footpath load creation")`) and `inputs.osi` (`geometry.footpath: "None"`, `footpath_width: 0.0`) to confirm that pedestrian live load was not applied to the bridge grillage model.
  - *Resolution:* In Table 2.4, footpath width is explicitly labeled `0.0 m (No footpath provided)`. In Table 3.4, the codal intensity is clarified: `Footpath Provided: None (Excluded from bridge layout)`, `Footpath Width: 0.0 m (No footpath)`, `Pedestrian Live Load Intensity: 4.905 kN/m² (IRC 6 Cl. 206.1 code provision; excluded from design — no footpath provided)`, and `Combination with Live Load: Not applied (no footpath provided in bridge cross-section)`.
- **IRC Publication Years Harmonization:**
  - *Resolution:* Reconciled all code publication citations across Section 8.1 (Table 8.1), Section 8.2 (Assumptions), Section 5.1, and Chapter 9 (References). Specifically harmonized `IRC 5 (2015)`, `IRC 22 (2015)`, and `IRC 112 (2020)` across all report sections to eliminate discrepancies and ensure 100% internal alignment.
- **End Diaphragm Utilization Charts:**
  - *Verification:* Confirmed that no dummy or fabricated utilization ratio chart is created for End Diaphragm. The three valid component charts (Plate Girders, Deck Slab, Cross Bracing) remain preserved, and the "Unavailable / Not Evaluated" status with technical rationale is clearly displayed in Table 5.28.

---

## 3. Comprehensive Viva Voce Defense Guide

### Q1: Why was `longtable` used instead of standard `table`?
> **Answer:** In LaTeX, the standard `table` / `tabular` environment creates an unbreakable vertical box. When tables exceed one page, they overflow past the bottom margin and get clipped. `longtable` breaks naturally across page boundaries, repeats headers (`\endhead`) on continuation pages, and provides running footers (`\endfoot`), essential for rigorous engineering reports.

### Q2: Why did `\caption{...}` throw `! Misplaced \noalign` in earlier versions?
> **Answer:** Inside `longtable`, `\caption` is an internal aligned cell. Without a trailing row break (`\\`), LaTeX encounters subsequent tokens (such as `\hline` or `\endfirsthead`) within the unclosed caption row, triggering `\noalign` syntax crashes. Appending `\\` terminates the caption row cleanly.

### Q3: What is the significance of the UR = 1.0 threshold line in Chapter 5?
> **Answer:** In structural engineering, $\text{UR} = \frac{\text{Demand}}{\text{Capacity}}$. A ratio $\le 1.0$ denotes compliance with limit-state criteria, while $\text{UR} > 1.0$ signifies failure. The dashed red line at $\text{UR} = 1.0$ provides an instant visual verification boundary for code compliance.

### Q4: Explain the difference between Longitudinal Interface Shear and Transverse Shear Capacity.
> **Answer:** In composite bridge girders (IRC 22 Cl. 606.10), horizontal shear flow across the steel-concrete interface must be transferred by shear studs into the concrete slab. The applied force is longitudinal shear per unit length ($V_L = \frac{V \cdot A \cdot \bar{y}}{I}$). The concrete slab resists this via transverse shear across potential failure planes ($V_{Rd} = c \cdot f_{ctd} \cdot A_{cv} + \mu \cdot \sigma_n + A_s \cdot f_{yd} \cdot \cos\alpha$). In Table 5.15, $V_L = 76.27\text{ kN/m}$ is resisted by $V_{Rd} = 999.28\text{ kN/m}$, giving $\text{UR} = 0.08$ (PASS).

### Q5: Why are End Diaphragm demand and capacity checks labeled "Unavailable / Not Evaluated" while Cross Bracing checks are populated?
> **Answer:** In the current OsdagBridge grillage analysis model, intermediate cross-bracing panels resist lateral loads distributed along the span (wind and seismic load cases) and generate resolved internal axial forces ($F_{diag}$ and $F_{chord}$). End diaphragms, however, are located directly at the support boundary nodes where lateral forces are transferred directly into the bearing reactions. Because member internal force extraction for support end diaphragms is not implemented in the current solver version, reporting demand/capacity values would be fabricated engineering data. OsdagBridge transparently reports the genuine member framing properties and slenderness checks while explicitly marking demand/capacity as "Unavailable / Not Evaluated".

### Q6: How was the shear stud connector quantity of 608 derived?
> **Answer:** Along the 30 m girder length, studs are placed at a longitudinal spacing of 395 mm per the interface shear calculation (IRC 22 Cl. 606.10). This gives $\text{int}(30{,}000 / 395) + 1 = 76$ sections along the bridge. With 2 studs per cross-section per girder across 4 girders, the total connector count is $76 \times 2 \times 4 = 608$ studs, yielding $0.0191\text{ m}^3$ of steel ($0.150\text{ MT}$).

### Q7: Why is pedestrian live load ($4.905\text{ kN/m}^2$) listed in Table 3.4 when Table 2.4 states no footpath is provided?
> **Answer:** Table 3.4 documents the codal pedestrian loading provision per IRC 6:2017 Clause 206.1 ($p = 4.905\text{ kN/m}^2$ for spans $\le 30\text{ m}$). However, because the bridge geometry specifies zero footpaths (`geometry.footpath: "None"` and `typical_section.footpath_width: 0.0`), the analysis engine skips footway load application. To ensure complete clarity and eliminate any ambiguity, Table 3.4 explicitly notes that the load is an IRC 6 reference provision and was not applied in the structural analysis combinations.

### Q8: How is the number of traffic lanes determined when not explicitly entered by the user?
> **Answer:** Under IRC 5:2015 Clause 104.3.1, a two-lane bridge without a raised median has a minimum carriageway width of $5.3\text{ m}$ (standard $7.0\text{ m}$ / $7.5\text{ m}$ with kerbs). With a user-defined carriageway width of $7.0\text{ m}$, the number of lanes is evaluated as 2, directly matching the 2-lane multi-lane live load factors and longitudinal braking force ($108.70\text{ kN}$) calculated under IRC 6 Clause 211.2.

---

## 4. Final Verification Checklists & Artifact Locations

- **Source Code Repository:** `C:\Users\lenovo\Desktop\Fossee OB\OsdagBridge`
- **Baseline Report:** `C:\Users\lenovo\Desktop\Fossee OB\Report_Before.pdf` (354 KB)
- **Enhanced Final Report:** `C:\Users\lenovo\Desktop\Fossee OB\Report_After.pdf` (1.46 MB, 66 total pages [1 cover + 65 content], 0 placeholders)
- **Technical Changes & Viva Guide:** `C:\Users\lenovo\Desktop\Fossee OB\Technical_Changes_and_Viva_Defense.md`
- **Git Status:** Clean modified set; no credentials, virtual environments, or temporary cache files staged; ready for review.
