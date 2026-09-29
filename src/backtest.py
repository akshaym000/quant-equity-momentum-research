"""Illustrative spread cost arithmetic, not a trading simulator."""
import numpy as np

def cost_sensitivity(gross_spread: float, round_trip_cost_bps=(0,5,10,25)):
    """Subtract assumed round-trip costs from a one-period quintile spread."""
    return [{"round_trip_cost_bps":int(cost),"gross_spread":gross_spread,"net_illustrative_spread":gross_spread-cost/10000 if np.isfinite(gross_spread) else np.nan} for cost in round_trip_cost_bps]
