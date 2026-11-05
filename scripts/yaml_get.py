#!/usr/bin/env python3
"""Print een waarde uit een YAML-bestand: yaml_get.py case.yaml rekenplek.cores

Lijsten komen op één regel per item. Een ontbrekende of lege waarde geeft een lege uitvoer.
"""
import sys

import yaml


def main():
    if len(sys.argv) != 3:
        sys.exit("gebruik: yaml_get.py <bestand> <sleutel.pad>")
    with open(sys.argv[1]) as f:
        value = yaml.safe_load(f)
    for key in sys.argv[2].split("."):
        value = value.get(key) if isinstance(value, dict) else None
    if value is None:
        return
    for item in value if isinstance(value, list) else [value]:
        print(item)


if __name__ == "__main__":
    main()
