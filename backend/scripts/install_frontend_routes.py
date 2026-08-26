#!/usr/bin/env python3
"""Idempotent patcher for frontend/src/App.js and Sidebar.jsx to wire the
Ops Center route + sidebar nav entry. Safe to run multiple times.

Usage (from /var/www/dialgenix/backend):
    python3 scripts/install_frontend_routes.py
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent  # /var/www/dialgenix
APP_JS = REPO / "frontend" / "src" / "App.js"
SIDEBAR = REPO / "frontend" / "src" / "components" / "Sidebar.jsx"


def patch(path: Path, marker: str, anchor: str, new_after_anchor: str) -> None:
    if not path.exists():
        print(f"SKIP: {path} not found", file=sys.stderr)
        return
    src = path.read_text()
    if marker in src:
        print(f"[patch] {path.name}: already patched.")
        return
    if anchor not in src:
        print(f"FATAL: anchor not found in {path}.\nWanted:\n{anchor}", file=sys.stderr)
        sys.exit(2)
    new_src = src.replace(anchor, anchor + new_after_anchor, 1)
    path.with_suffix(path.suffix + ".bak.ops").write_text(src)
    path.write_text(new_src)
    print(f"[patch] {path.name}: applied.")


# 1. App.js — add import + route
patch(
    APP_JS,
    marker="OpsCenterPage",
    anchor='import ROICalculatorPage from "@/pages/ROICalculatorPage";',
    new_after_anchor='\nimport OpsCenterPage from "@/pages/OpsCenterPage";',
)
patch(
    APP_JS,
    marker='path="/ops"',
    anchor='<Route path="/analytics" element={<AnalyticsPage />} />',
    new_after_anchor='\n                    <Route path="/ops" element={<OpsCenterPage />} />',
)

# 2. Sidebar.jsx — add Activity icon + nav entry
patch(
    SIDEBAR,
    marker="Activity",
    anchor="Database, Shield, Rocket, User, Filter, Star",
    new_after_anchor=", Activity",
)
patch(
    SIDEBAR,
    marker='"/app/ops"',
    anchor='{ path: "/app/analytics", icon: TrendingUp, label: "Analytics" },',
    new_after_anchor='\n    { path: "/app/ops", icon: Activity, label: "Ops Center" },',
)
print("[install_frontend_routes] Done.")
