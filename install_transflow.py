"""
install_transflow.py
====================
Installiert die "TransFlow in CPT Destinations" Erweiterung in UFO-Engine.

Zeigt PPTransFlow-Volumen (Einheiten + Cases + Bins) aufgeteilt nach Pick H1
und H3 in jedem CPT-Card der CPT Destinations Karte an.

Idempotent: überspringt bereits installierte Teile.
Ausgelegt für frische UFO-Engine Installationen (ungepatcht).

Aufruf (aus dem Ordner C:\\UFO-Engine):
    .venv\\Scripts\\python.exe C:\\Meiner\\Ufoneues\\install_transflow.py
"""
import sys
from pathlib import Path

ROOT = Path("C:/UFO-Engine")
ok = True


def replace_block(path_rel, old_block, new_block, check):
    global ok
    p = ROOT / path_rel
    c = p.read_text(encoding="utf-8")
    if check in c:
        print(f"  SKIP {path_rel}: bereits vorhanden"); return
    if old_block not in c:
        print(f"  FEHLER {path_rel}: Alter Block nicht gefunden"); ok = False; return
    p.write_text(c.replace(old_block, new_block, 1), encoding="utf-8")
    print(f"  OK   {path_rel}")


def replace_either(path_rel, old1, old2, new_block, check):
    """Versucht old1, dann old2 — für Dateien die evtl. halb installiert sind."""
    global ok
    p = ROOT / path_rel
    c = p.read_text(encoding="utf-8")
    if check in c:
        print(f"  SKIP {path_rel}: bereits vorhanden"); return
    for old in (old1, old2):
        if old and old in c:
            p.write_text(c.replace(old, new_block, 1), encoding="utf-8")
            print(f"  OK   {path_rel}"); return
    print(f"  FEHLER {path_rel}: Alter Block nicht gefunden"); ok = False


print("TransFlow CPT Installer")
print("========================")

# ── 1. rodeo_cpt.py: _try_pp_h3 → _try_pp mit TransFlow-Extraktion ─────────
print("\n1. _try_pp + trans_flow_by_cpt (rodeo_cpt.py)")
replace_block(
    "backend/services/rodeo_cpt.py",
    '    def _try_pp_h3(url: str, cpt_col: str = "ExSD") -> dict:\n'
    '        """Fetch PP-axis CSV and return only H3 entries keyed by (dest, cpt)."""\n'
    '        try:\n'
    '            by_pp = _aggregate_by_pp(_fetch_csv(url, cookie_str, None), cpt_col=cpt_col)\n'
    '        except RuntimeError:\n'
    '            return {}\n'
    '        result: dict[tuple[str, str], int] = {}\n'
    '        for (pp, cpt), qty in by_pp.items():\n'
    '            if not _is_h3_pp(pp):\n'
    '                continue\n'
    '            m = _RE_PP_DEST_SVC.match(pp)\n'
    '            if not m:\n'
    '                continue\n'
    '            key = (m.group(1), cpt)           # (dest, cpt)\n'
    '            result[key] = result.get(key, 0) + qty\n'
    '        return result\n'
    '\n'
    '    # 1+2: DEST-axis totals -- use NYP pools to match cases filter\n'
    '    try:\n'
    '        total_keys = _aggregate(\n'
    '            _fetch_csv(_NYP_UNITS_URL, cookie_str, None), cpt_col="ExSD"\n'
    '        )\n'
    '    except RuntimeError as e:\n'
    '        return {"cpts": [], "fetched_at": now, "error": str(e)}\n'
    '\n'
    '    total_cases = _try_dest(RODEO_CASES_URL, "MinExSD")\n'
    '    total_unc   = _try_dest(RODEO_UNCONSTRAINED_CASES_URL, "MinExSD")\n'
    '\n'
    '    # 3+4: PP-axis, H3 only (one broad + one cases)\n'
    '    h3_keys  = _try_pp_h3(_NYP_UNITS_BY_PP_URL,  "ExSD")\n'
    '    h3_cases = _try_pp_h3(_CPT_CASES_BY_PP_URL,  "MinExSD")\n'
    '    h3_unc   = _try_pp_h3(_CPT_UNC_CASES_BY_PP_URL, "MinExSD")',
    '    def _try_pp(url: str, cpt_col: str = "ExSD") -> tuple:\n'
    '        """Fetch PP-axis CSV. Returns (h3_by_dest_cpt, trans_flow_by_cpt).\n'
    '\n'
    '        h3_by_dest_cpt  = {(dest, cpt): qty}  -- H3/PUP paths only\n'
    '        trans_flow_by_cpt = {cpt: qty}         -- PPTransFlow* paths\n'
    '        """\n'
    '        try:\n'
    '            by_pp = _aggregate_by_pp(_fetch_csv(url, cookie_str, None), cpt_col=cpt_col)\n'
    '        except RuntimeError:\n'
    '            return {}, {}\n'
    '        h3_result: dict[tuple[str, str], int] = {}\n'
    '        tf_result: dict[str, int]             = {}\n'
    '        for (pp, cpt), qty in by_pp.items():\n'
    '            if "flow" in pp.lower():\n'
    '                tf_result[cpt] = tf_result.get(cpt, 0) + qty\n'
    '                continue\n'
    '            if not _is_h3_pp(pp):\n'
    '                continue\n'
    '            m = _RE_PP_DEST_SVC.match(pp)\n'
    '            if not m:\n'
    '                continue\n'
    '            h3_result[(m.group(1), cpt)] = h3_result.get((m.group(1), cpt), 0) + qty\n'
    '        return h3_result, tf_result\n'
    '\n'
    '    # 1+2: DEST-axis totals -- use NYP pools to match cases filter\n'
    '    try:\n'
    '        total_keys = _aggregate(\n'
    '            _fetch_csv(_NYP_UNITS_URL, cookie_str, None), cpt_col="ExSD"\n'
    '        )\n'
    '    except RuntimeError as e:\n'
    '        return {"cpts": [], "fetched_at": now, "error": str(e)}\n'
    '\n'
    '    total_cases = _try_dest(RODEO_CASES_URL, "MinExSD")\n'
    '    total_unc   = _try_dest(RODEO_UNCONSTRAINED_CASES_URL, "MinExSD")\n'
    '\n'
    '    # 3+4: PP-axis -- H3 destinations + TransFlow (same fetch, no extra requests)\n'
    '    h3_keys,  tf_units = _try_pp(_NYP_UNITS_BY_PP_URL,  "ExSD")\n'
    '    h3_cases, tf_cases = _try_pp(_CPT_CASES_BY_PP_URL,  "MinExSD")\n'
    '    h3_unc             = _try_pp(_CPT_UNC_CASES_BY_PP_URL, "MinExSD")[0]\n'
    '\n'
    '    # Build trans_flow_by_cpt: units + cases per CPT for PPTransFlow*\n'
    '    all_tf_cpts = set(tf_units) | set(tf_cases)\n'
    '    trans_flow_by_cpt = {\n'
    '        cpt: {"units": tf_units.get(cpt, 0), "cases": tf_cases.get(cpt, 0)}\n'
    '        for cpt in all_tf_cpts\n'
    '        if tf_units.get(cpt, 0) > 0 or tf_cases.get(cpt, 0) > 0\n'
    '    }',
    "_try_pp",
)

# ── 2. rodeo_cpt.py: Pallet-Breakdown-Aufruf vor "Build H1 and H3 rows" ─────
print("\n2. fetch_transflow_pallet_breakdown Aufruf (rodeo_cpt.py)")
replace_block(
    "backend/services/rodeo_cpt.py",
    '    }\n'
    '\n'
    '    # Build H1 and H3 rows',
    '    }\n'
    '\n'
    '    # 5: Pallet-slot breakdown for PPTransFlow (H1 P-1..P-4, H3 P-1)\n'
    '    trans_flow_pallets_by_cpt = fetch_transflow_pallet_breakdown(cookie_str)\n'
    '\n'
    '    # Build H1 and H3 rows',
    "fetch_transflow_pallet_breakdown(cookie_str)",
)

# ── 3. rodeo_cpt.py: Return mit trans_flow_pallets_by_cpt ───────────────────
print("\n3. Return mit beiden TransFlow-Feldern (rodeo_cpt.py)")
replace_block(
    "backend/services/rodeo_cpt.py",
    '    cpts_out.sort(key=lambda x: (x["cpt"], x["dest"], x["hall"]))\n'
    '    return {"cpts": cpts_out, "fetched_at": now, "error": None}\n'
    '\ndef fetch_cpt_destinations',
    '    cpts_out.sort(key=lambda x: (x["cpt"], x["dest"], x["hall"]))\n'
    '    return {"cpts": cpts_out, "fetched_at": now, "error": None,\n'
    '            "trans_flow_by_cpt": trans_flow_by_cpt,\n'
    '            "trans_flow_pallets_by_cpt": trans_flow_pallets_by_cpt}\n'
    '\ndef fetch_cpt_destinations',
    "trans_flow_pallets_by_cpt",
)

# ── 4. rodeo_cpt.py: _TF_PALLET_ITEM_URL Konstante ──────────────────────────
print("\n4. _TF_PALLET_ITEM_URL Konstante (rodeo_cpt.py)")
replace_block(
    "backend/services/rodeo_cpt.py",
    '"&shipmentType=TRANSSHIPMENTS"\n'
    ')\n'
    '\n'
    '\n'
    '# Cases by process path',
    '"&shipmentType=TRANSSHIPMENTS"\n'
    ')\n'
    '\n'
    '\n'
    '# ItemListCSV filtered to PPTransFlow — for pallet-slot breakdown per CPT.\n'
    '# Outer Scannable ID P-1..P-4 = H1 pallet slots; Outer Outer Scannable ID P-1 = H3.\n'
    '# NYP pools only (PickingNotYetPicked + Prioritized) — open backlog only.\n'
    '_TF_PALLET_ITEM_URL = (\n'
    '    "https://rodeo-dub.amazon.com/DRS8/ItemListCSV"\n'
    '    "?_enabledColumns=on"\n'
    '    "&enabledColumns=OUTER_OUTER_SCANNABLE_ID"\n'
    '    "&enabledColumns=OUTER_SCANNABLE_ID"\n'
    '    "&ProcessPath=PPTransFlow"\n'
    '    "&shipmentTypes=TRANSSHIPMENTS"\n'
    '    "&workPool=PickingNotYetPicked"\n'
    '    "&workPool=PickingNotYetPickedPrioritized"\n'
    '    "&_workPool=on"\n'
    '    "&exSDRange.quickRange=ALL"\n'
    '    "&shipmentType=TRANSSHIPMENTS"\n'
    ')\n'
    '\n'
    '\n'
    '# Cases by process path',
    "_TF_PALLET_ITEM_URL",
)

# ── 5. rodeo_cpt.py: fetch_transflow_pallet_breakdown Funktion ───────────────
print("\n5. fetch_transflow_pallet_breakdown Funktion (rodeo_cpt.py)")
replace_block(
    "backend/services/rodeo_cpt.py",
    '    return out\n'
    '\n'
    '\n'
    'def compare_not_picked_promotion(',
    '    return out\n'
    '\n'
    '\n'
    '\n'
    'def fetch_transflow_pallet_breakdown(cookie_str: str | None = None) -> dict[str, dict]:\n'
    '    """Per-CPT pallet-slot breakdown for PPTransFlow items (open NYP backlog).\n'
    '\n'
    '    Returns {cpt_str: {"h1": units, "h3": units, "h1_bins": N, "h3_bins": N,\n'
    '                       "h1_cases": N, "h3_cases": N}} where:\n'
    '      h1       = units where Outer Scannable ID starts with P-1..P-4\n'
    '      h3       = units where Outer Outer Scannable ID starts with P-1\n'
    '      h1_bins  = distinct Outer Scannable ID values in P-1..P-4 (one bin per unique ID)\n'
    '      h3_bins  = distinct Outer Outer Scannable ID values starting with P-1\n'
    '      h1_cases = distinct Scannable ID values for H1 items (inner tote/case count)\n'
    '      h3_cases = row count for H3 items (each row = one case; Scannable ID is empty for H3)\n'
    '\n'
    '    cpt_str format matches fetch_cpt_destinations_by_hall: "YYYY-MM-DD HH:MM"\n'
    '    """\n'
    '    if cookie_str is None:\n'
    '        cookie_str = _get_firefox_cookies("rodeo-dub.amazon.com")\n'
    '    if not cookie_str:\n'
    '        return {}\n'
    '    try:\n'
    '        rows = _fetch_csv(_TF_PALLET_ITEM_URL, cookie_str, None)\n'
    '    except RuntimeError:\n'
    '        return {}\n'
    '\n'
    '    _H1_PREFIXES = ("P-1", "P-2", "P-3", "P-4")\n'
    '    # Intermediate: collect sets of distinct IDs per CPT\n'
    '    bins_h1:  dict[str, set] = {}   # outer P-slots for H1\n'
    '    bins_h3:  dict[str, set] = {}   # outer outer P-slots for H3\n'
    '    cases_h1: dict[str, set] = {}   # inner tote/case IDs for H1 (distinct Scannable ID)\n'
    '    # h3_cases counted as rows: H3 Scannable IDs are empty; each row = one case\n'
    '    result: dict[str, dict] = {}\n'
    '    for row in rows:\n'
    '        cpt_raw = _cell(row, "Need To Ship By Date")\n'
    '        if not cpt_raw:\n'
    '            continue\n'
    '        cpt_str = cpt_raw[:16]   # "YYYY-MM-DD HH:MM"\n'
    '        try:\n'
    '            qty = int(_cell(row, "Quantity").replace(",", "") or "0")\n'
    '        except ValueError:\n'
    '            continue\n'
    '        if qty <= 0:\n'
    '            continue\n'
    '        outer     = _cell(row, "Outer Scannable ID").upper()\n'
    '        outer_out = _cell(row, "Outer Outer Scannable ID").upper()\n'
    '        inner     = _cell(row, "Scannable ID").upper()\n'
    '        slot = result.setdefault(cpt_str, {"h1": 0, "h3": 0, "h1_bins": 0, "h3_bins": 0, "h1_cases": 0, "h3_cases": 0})\n'
    '        if outer.startswith(_H1_PREFIXES):\n'
    '            slot["h1"] += qty\n'
    '            bins_h1.setdefault(cpt_str, set()).add(outer)\n'
    '            if inner:\n'
    '                cases_h1.setdefault(cpt_str, set()).add(inner)\n'
    '        if outer_out.startswith("P-1"):\n'
    '            slot["h3"] += qty\n'
    '            slot["h3_cases"] += 1   # each row = one container/case (Scannable ID is empty for H3)\n'
    '            bins_h3.setdefault(cpt_str, set()).add(outer_out)\n'
    '\n'
    '    # Resolve distinct counts\n'
    '    for cpt_str, slot in result.items():\n'
    '        slot["h1_bins"]  = len(bins_h1.get(cpt_str, set()))\n'
    '        slot["h3_bins"]  = len(bins_h3.get(cpt_str, set()))\n'
    '        slot["h1_cases"] = len(cases_h1.get(cpt_str, set()))\n'
    '        # h3_cases already accumulated as row count above\n'
    '    return result\n'
    '\n'
    '\n'
    'def compare_not_picked_promotion(',
    "def fetch_transflow_pallet_breakdown",
)

# ── 6. useOverview.ts: CptDestByHall Interface ──────────────────────────────
print("\n6. CptDestByHall Interface (useOverview.ts)")
replace_block(
    "frontend/src/api/hooks/useOverview.ts",
    "export interface CptDestByHall {\n"
    "  cpts:       { cpt: string; dest: string; hall: 'h1' | 'h3'; units: number; total_units: number; cases: number; cases_open: number; cases_unconstrained: number }[]\n"
    "  fetched_at: string\n"
    "  error:      string | null\n"
    "}",
    "export interface CptDestByHall {\n"
    "  cpts:                       { cpt: string; dest: string; hall: 'h1' | 'h3'; units: number; total_units: number; cases: number; cases_open: number; cases_unconstrained: number }[]\n"
    "  trans_flow_by_cpt?:         Record<string, { units: number; cases: number }>\n"
    "  trans_flow_pallets_by_cpt?: Record<string, { h1: number; h3: number; h1_bins: number; h3_bins: number; h1_cases: number; h3_cases: number }>\n"
    "  fetched_at: string\n"
    "  error:      string | null\n"
    "}",
    "trans_flow_pallets_by_cpt?",
)

# ── 7. OBOverview.tsx: CptDestPanelProps Interface ──────────────────────────
print("\n7. CptDestPanelProps Interface (OBOverview.tsx)")
replace_block(
    "frontend/src/pages/OBOverview.tsx",
    "  hallCpts?:         CptDestByHall['cpts']\n"
    "}",
    "  hallCpts?:         CptDestByHall['cpts']\n"
    "  transFlowByCpt?:        Record<string, { units: number; cases: number }>\n"
    "  transFlowPalletsByCpt?: Record<string, { h1: number; h3: number; h1_bins: number; h3_bins: number; h1_cases: number; h3_cases: number }>\n"
    "}",
    "transFlowPalletsByCpt?",
)

# ── 8. OBOverview.tsx: Funktionssignatur ────────────────────────────────────
print("\n8. CptDestPanel Signatur (OBOverview.tsx)")
replace_block(
    "frontend/src/pages/OBOverview.tsx",
    "function CptDestPanel({ cpts: rawCpts, fetchedAt, error, fetching, onRefresh, "
    "pickHcRows, pickerPaths: rawPickerPaths, workforceByDest, pickHall, allPaths, hallCpts }: CptDestPanelProps) {",
    "function CptDestPanel({ cpts: rawCpts, fetchedAt, error, fetching, onRefresh, "
    "pickHcRows, pickerPaths: rawPickerPaths, workforceByDest, pickHall, allPaths, hallCpts, transFlowByCpt, transFlowPalletsByCpt }: CptDestPanelProps) {",
    "transFlowPalletsByCpt }",
)

# ── 9. OBOverview.tsx: TransFlow-Block im CPT-Card ──────────────────────────
print("\n9. TransFlow-Block (Einh. + Cases + Bins) im CPT-Card (OBOverview.tsx)")
replace_either(
    "frontend/src/pages/OBOverview.tsx",
    # Alt 1: frische Installation (kein TransFlow-Block vorhanden)
    "                        {(() => { const visibleRows = rows; return (\n"
    "                        <div className=\"border-t border-slate-700/60 pt-2 space-y-1.5\">\n"
    "                          {visibleRows.map(r => {",
    # Alt 2: alter Install-Block (nur Einh. + Cases, kein Bins)
    "                        {(() => {\n"
    "                          const tf = transFlowByCpt?.[cpt]\n"
    "                          return tf && (tf.units > 0 || tf.cases > 0) ? (\n"
    "                            <div className=\"border-t border-slate-700/60 pt-1.5\">\n"
    "                              <div className=\"flex items-center justify-between gap-1\">\n"
    "                                <span className=\"font-mono text-[10px] text-violet-400 shrink-0\">TransFlow</span>\n"
    "                                <div className=\"text-right tabular-nums flex-1 min-w-0\">\n"
    "                                  <span className=\"font-semibold text-sm text-violet-300\">{tf.units.toLocaleString('de-DE')}</span>\n"
    "                                  <span className=\"text-[10px] text-slate-500\"> Einh.</span>\n"
    "                                  <div className=\"text-slate-500 text-[10px] leading-tight\">{tf.cases.toLocaleString('de-DE')} Cases</div>\n"
    "                                </div>\n"
    "                              </div>\n"
    "                            </div>\n"
    "                          ) : null\n"
    "                        })()}\n"
    "\n"
    "                        {(() => { const visibleRows = rows; return (\n"
    "                        <div className=\"border-t border-slate-700/60 pt-2 space-y-1.5\">\n"
    "                          {visibleRows.map(r => {",
    # NEU (beide Alternativen werden durch diesen Block ersetzt)
    "{(() => {\n"
    "                          const tf = transFlowByCpt?.[cpt]\n"
    "                          const tfp = transFlowPalletsByCpt?.[cpt]\n"
    "                          if (!tf || (tf.units === 0 && tf.cases === 0)) return null\n"
    "                          const pallH1    = tfp?.h1       ?? 0\n"
    "                          const pallH3    = tfp?.h3       ?? 0\n"
    "                          const casesH1   = tfp?.h1_cases ?? 0\n"
    "                          const casesH3   = tfp?.h3_cases ?? 0\n"
    "                          return (\n"
    "                            <div className=\"border-t border-slate-700/60 pt-1.5\">\n"
    "                              <div className=\"flex items-center justify-between gap-1\">\n"
    "                                <span className=\"font-mono text-[10px] text-violet-400 shrink-0\">TransFlow</span>\n"
    "                                <div className=\"text-right tabular-nums flex-1 min-w-0\">\n"
    "                                  {pickHall !== 'h3' && (\n"
    "                                    <div className=\"leading-tight\">\n"
    "                                      <span className=\"font-semibold text-sm text-violet-300\">{pallH1.toLocaleString('de-DE')}</span>\n"
    "                                      <span className=\"text-[10px] text-slate-500\"> Einh.</span>\n"
    "                                    </div>\n"
    "                                  )}\n"
    "                                  {pickHall !== 'h1' && (\n"
    "                                    <div className=\"leading-tight\">\n"
    "                                      <span className=\"font-semibold text-sm text-violet-300\">{pallH3.toLocaleString('de-DE')}</span>\n"
    "                                      <span className=\"text-[10px] text-slate-500\"> Einh.</span>\n"
    "                                    </div>\n"
    "                                  )}\n"
    "                                  {pickHall !== 'h3' && (\n"
    "                                    <div className=\"text-violet-400/70 text-[10px] leading-tight\">{casesH1.toLocaleString('de-DE')} Cases</div>\n"
    "                                  )}\n"
    "                                  {pickHall !== 'h1' && (\n"
    "                                    <div className=\"text-violet-400/70 text-[10px] leading-tight\">{casesH3.toLocaleString('de-DE')} Cases</div>\n"
    "                                  )}\n"
    "                                  {pickHall !== 'h3' && (\n"
    "                                    <div className=\"text-violet-400/70 text-[10px] leading-tight\">{(tfp?.h1_bins ?? 0).toLocaleString('de-DE')} Bins</div>\n"
    "                                  )}\n"
    "                                  {pickHall !== 'h1' && (\n"
    "                                    <div className=\"text-violet-400/70 text-[10px] leading-tight\">{(tfp?.h3_bins ?? 0).toLocaleString('de-DE')} Bins</div>\n"
    "                                  )}\n"
    "                                </div>\n"
    "                              </div>\n"
    "                            </div>\n"
    "                          )\n"
    "                        })()}\n"
    "\n"
    "                        {(() => { const visibleRows = rows; return (\n"
    "                        <div className=\"border-t border-slate-700/60 pt-2 space-y-1.5\">\n"
    "                          {visibleRows.map(r => {",
    "h1_cases",
)

# ── 10. OBOverview.tsx: Props im CptDestPanel-Aufruf ────────────────────────
print("\n10. transFlowByCpt + transFlowPalletsByCpt Props (CptDestPanel-Aufruf)")
replace_either(
    "frontend/src/pages/OBOverview.tsx",
    # Alt 1: frische Installation (kein transFlowByCpt)
    "                hallCpts={cptByHallData?.cpts ?? []}\n"
    "                allPaths={allPathsData?.paths ?? []}\n"
    "                pickHall={pickHall}\n"
    "              />",
    # Alt 2: alter Install-Block (nur transFlowByCpt)
    "                hallCpts={cptByHallData?.cpts ?? []}\n"
    "                allPaths={allPathsData?.paths ?? []}\n"
    "                pickHall={pickHall}\n"
    "                transFlowByCpt={cptByHallData?.trans_flow_by_cpt}\n"
    "              />",
    # NEU
    "                hallCpts={cptByHallData?.cpts ?? []}\n"
    "                allPaths={allPathsData?.paths ?? []}\n"
    "                pickHall={pickHall}\n"
    "                transFlowByCpt={cptByHallData?.trans_flow_by_cpt}\n"
    "                transFlowPalletsByCpt={cptByHallData?.trans_flow_pallets_by_cpt}\n"
    "              />",
    "transFlowPalletsByCpt={cptByHallData",
)

# ── Ergebnis ─────────────────────────────────────────────────────────────────
print()
if ok:
    print("✓ Installation erfolgreich!")
    print("  → Backend neu starten")
    print("  → Browser Hard-Refresh (Strg+Shift+R)")
    print()
    print("  TransFlow erscheint in jedem CPT-Card (violett) wenn PPTransFlow")
    print("  Volumen für die jeweilige CPT-Uhrzeit vorhanden ist.")
    print("  Zeigt: Einh. / Cases / Bins — getrennt für Pick H1 und Pick H3.")
else:
    print("✗ Es gab Fehler — siehe oben")
    sys.exit(1)
