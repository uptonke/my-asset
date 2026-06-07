"""v4.4 backend split placeholder: data fetch boundary.

This module is intentionally small and side-effect free. It documents the target
boundary before moving executable code out of update_stock_meta.py.
"""
from __future__ import annotations

MODULE_ID = "data_fetch"
OWNED_CONCERNS = ["market data retrieval", "raw price input", "ticker metadata input"]
SIDE_EFFECTS_ALLOWED = False
