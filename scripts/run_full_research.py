"""Run the full research pipeline on user-supplied market data."""
import argparse, sys, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))

def main():
    p=argparse.ArgumentParser(); p.add_argument("--config",default=str(ROOT/"config.json")); args=p.parse_args()
    cfg=json.loads(Path(args.config).read_text(encoding="utf-8"))
    data_path=ROOT/cfg["data_path"]
    if not data_path.exists():
        raise FileNotFoundError(f"Market data not found: {data_path}. Provide a CSV with date,ticker,adj_close,volume columns; see README.md.")
    from research import run
    run(data_path,ROOT/"results",cfg["research_fraction"],cfg["validation_fraction"],cfg["cost_bps_round_trip"],cfg["meaningful_spread"],cfg["date_column"],cfg["ticker_column"],cfg["adjusted_close_column"],cfg["volume_column"])
    print(f"Research outputs written to {ROOT/'results'}")
if __name__=="__main__": main()
