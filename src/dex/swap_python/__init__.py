"""
This Swapper is written in Python and not as reliable as src/engine/rusted_math's smart router.
Only for OSR, for quick filtering for smart router v1(One Way), v2(IA5).
It is supposed that smart router v3(Convex) won't use OSR.
"""

from src.dex.swap_python.swap import Swap, SwapParamsTD

__all__ = ["Swap", "SwapParamsTD"]