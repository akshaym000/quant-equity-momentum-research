import pandas as pd
from features import build_features,chronological_splits

def test_future_perturbation_cannot_change_past_feature():
    x=pd.DataFrame({"date":pd.date_range("2020-01-01",periods=8),"ticker":"A","adj_close":[10,11,12,13,14,15,16,17],"volume":10})
    a=build_features(x,lookbacks=(1,),horizons=(1,)); x.loc[7,"adj_close"]=10000; b=build_features(x,lookbacks=(1,),horizons=(1,))
    assert a.loc[:5,"past_1d"].equals(b.loc[:5,"past_1d"])
    assert a.loc[6,"future_1d"]!=b.loc[6,"future_1d"]

def test_chronological_split_has_disjoint_dates():
    x=pd.DataFrame({"date":pd.date_range("2020-01-01",periods=20).repeat(2)})
    parts=chronological_splits(x)
    sets=[set(p.date) for p in parts]
    assert not (sets[0]&sets[1] or sets[1]&sets[2] or sets[0]&sets[2])
