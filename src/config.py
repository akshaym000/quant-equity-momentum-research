"""Read the fixed YAML configuration used by command-line entry points."""
from pathlib import Path
import json

def load_config(path: str | Path) -> dict:
    """Load a YAML mapping and reject empty or non-mapping configurations."""
    values=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(values,dict): raise ValueError("Configuration must be a JSON object")
    return values
