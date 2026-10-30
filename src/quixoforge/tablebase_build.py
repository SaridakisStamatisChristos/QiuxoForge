"""Developer-only reproducible 3x3 tablebase materialization.

Run: PYTHONPATH=src python -m quixoforge.tablebase_build
Does not mutate code or checksums; prints source digest for release audit.
"""
from pathlib import Path
import json
from .tablebase import generate


def main():
    data, report = generate()
    path = Path(__file__).parent / 'data' / 'quixo3.tbl.gz'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(data)
    print(json.dumps(report,sort_keys=True))


if __name__ == '__main__': main()
