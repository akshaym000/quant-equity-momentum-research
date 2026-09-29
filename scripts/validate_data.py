import argparse,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
from data_loader import load_csv
from data_validation import validate_data
p=argparse.ArgumentParser(); p.add_argument("path",nargs="?",default=None); a=p.parse_args(); cfg=json.loads((ROOT/"config.json").read_text(encoding="utf-8")); path=a.path or ROOT/cfg["data_path"]; print(json.dumps(validate_data(load_csv(path,cfg["date_column"],cfg["ticker_column"],cfg["adjusted_close_column"],cfg["volume_column"])),indent=2))
