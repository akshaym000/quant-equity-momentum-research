import pandas as pd
from features import build_features

def test_lagged_and_forward_calculations():
    x=pd.DataFrame({"date":pd.date_range("2024-01-01",periods=8),"ticker":"A","adj_close":[100,101,102,103,104,105,106,107],"volume":100})
    f=build_features(x,lookbacks=(1,),horizons=(1,))
    assert abs(f.loc[2,"past_1d"]-(102/101-1))<1e-12
    assert abs(f.loc[2,"future_1d"]-(103/102-1))<1e-12
    assert pd.isna(f.loc[7,"future_1d"])
