import pandas as pd
from inference import welch_comparison

def test_insufficient_cross_section_reports_nan():
    x=pd.DataFrame({"past_5d":[.1,.2],"future_5d":[.01,.02],"date":["2020-01-01"]*2})
    assert pd.isna(welch_comparison(x)["p_value"])
