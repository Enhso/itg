"""Generate the committed synthetic example batch."""

from __future__ import annotations

import argparse
from pathlib import Path

from itg.examples import generate_examples


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("data/examples"))
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--first-seed", type=int, default=1)
    args = parser.parse_args()
    generate_examples(args.output_dir, count=args.count, first_seed=args.first_seed)


if __name__ == "__main__":
    main()
