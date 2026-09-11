# -*- coding: utf-8 -*-
"""Deprecated location shim (temporary).

The implementation moved to reproduction/analysis/analyze_volatility_regimes.py.
This stub exists only so an in-flight reproduction batch (started 2026-09-11)
can finish; it is scheduled for removal afterwards. Use the new path instead.
"""
import os
import runpy

_HERE = os.path.dirname(os.path.abspath(__file__))
_TARGET = os.path.join(os.path.dirname(_HERE), "reproduction", "analysis",
                       "analyze_volatility_regimes.py")
runpy.run_path(_TARGET, run_name="__main__")
