import pandas as pd
import pytest
from data_validation import validate_data

def panel(): return pd.DataFrame({"date":["2020-01-01","2020-01-02"],"ticker":["A","A"],"adj_close":[10,11],"volume":[2,3]})
def test_valid_panel(): assert validate_data(panel())["rows"]==2
def test_duplicate_rejected():
    x=pd.concat([panel(),panel().iloc[[0]]])
    with pytest.raises(ValueError,match="Duplicate"): validate_data(x)
def test_nonpositive_price_rejected():
    x=panel(); x.loc[0,"adj_close"]=0
    with pytest.raises(ValueError,match="positive"): validate_data(x)
