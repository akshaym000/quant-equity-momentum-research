"""Small plotting and output helpers."""
from pathlib import Path
import matplotlib.pyplot as plt

def save_primary_figures(df, quintiles, spec, out: Path, splits=None):
    out.mkdir(parents=True,exist_ok=True)
    df.past_5d.dropna().hist(bins=60); plt.title("Lagged 5-session return distribution"); plt.xlabel("Return"); plt.ylabel("Count"); plt.tight_layout(); plt.savefig(out/"past_5d_distribution.png"); plt.close()
    plt.errorbar(quintiles.quintile,quintiles["mean"],yerr=1.96*quintiles["std"]/(quintiles.n**.5),fmt="o-"); plt.title("Future 5-session return by quintile (naive 95% intervals)"); plt.xlabel("Signal quintile"); plt.ylabel("Mean future return"); plt.tight_layout(); plt.savefig(out/"future_5d_by_quintile.png"); plt.close()
    s=df[["past_5d","future_5d"]].dropna(); plt.hexbin(s.past_5d,s.future_5d,gridsize=45,mincnt=1); plt.xlabel("Past 5-session return"); plt.ylabel("Future 5-session return"); plt.title("Past vs future return (descriptive)"); plt.colorbar(label="Observations"); plt.tight_layout(); plt.savefig(out/"past_vs_future_hexbin.png"); plt.close()
    matrix=spec.pivot(index="lookback",columns="horizon",values="p_fdr_bh")
    plt.imshow(matrix.to_numpy(),aspect="auto",cmap="viridis_r"); plt.xticks(range(len(matrix.columns)),matrix.columns); plt.yticks(range(len(matrix.index)),matrix.index); plt.xlabel("Forward horizon (sessions)"); plt.ylabel("Trailing lookback (sessions)"); plt.title("Exploratory grid: BH adjusted p-values"); plt.colorbar(label="Adjusted p-value"); plt.tight_layout(); plt.savefig(out/"exploratory_fdr_heatmap.png"); plt.close()
    if splits is not None:
        names=[r["split"] for r in splits]; values=[r.get("spread",float("nan")) for r in splits]
        plt.bar(names,values); plt.axhline(0,color="black",linewidth=.8); plt.ylabel("Top-minus-bottom spread"); plt.title("Chronological comparison (each segment reported once)"); plt.xticks(rotation=15); plt.tight_layout(); plt.savefig(out/"chronological_spreads.png"); plt.close()
