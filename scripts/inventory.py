import argparse
import json
from pathlib import Path
from lastcopy.config import Settings
from lastcopy.inventory import inventory

parser = argparse.ArgumentParser()
parser.add_argument("archive", type=Path)
args = parser.parse_args()
print(inventory(args.archive.read_bytes(), Settings.load()).model_dump_json(indent=2))
