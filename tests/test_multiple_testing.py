import pandas as pd
from multiple_testing import adjust_pvalues

def test_adjustments_are_not_smaller_than_raw_p():
    x=adjust_pvalues(pd.DataFrame({"p_value":[.01,.04,.5]}))
    assert (x.p_bonferroni>=x.p_value).all()
    assert (x.p_fdr_bh>=x.p_value).all()
