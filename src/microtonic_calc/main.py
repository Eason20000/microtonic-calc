import argparse
import json

from tabulate import tabulate

from microtonic_calc.calc import compute_edo
from microtonic_calc.cli import add_common_args, is_custom, resolve

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def main():
    parser = argparse.ArgumentParser(
        description="Calculate n-EDO Scale Tune parameters"
    )
    add_common_args(parser, edo_required=True)
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args()

    p = resolve(args)
    result = compute_edo(
        args.edo, p["range_neg"], p["range_pos"], p["step"], args.max_channels
    )

    if args.output == "json":
        print(json.dumps(result))
        return

    label = "custom" if is_custom(args) else args.preset
    data = result["data"]

    print(f"\n=== {result['edo']}-EDO (preset: {label}) ===")
    print(f"step: {result['step']}, bias: {result['bias']}")
    print(f"Channels required: {len(data)}\n")

    header = ["note"] + [f"ch{i}" for i in range(len(data))]
    rows = [
        [name] + [str(ch[ni]) if ch[ni] is not None else "N/A" for ch in data]
        for ni, name in enumerate(NOTE_NAMES)
    ]
    print("Per-channel offsets:")
    print(tabulate([header] + rows, tablefmt="grid"))
    print()

    rows = [[d["degree"], d["channel"], d["semitone"]] for d in result["map"]]
    print("Mapping (degree -> channel, semitone):")
    print(tabulate([["deg", "ch", "semitone"]] + rows, tablefmt="grid"))


if __name__ == "__main__":
    main()
