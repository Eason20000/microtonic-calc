import argparse
import json
from os.path import basename

from tabulate import tabulate

from microtonic_calc.calc import compute_scale
from microtonic_calc.cli import (
    add_common_args,
    is_custom,
    load_scale,
    resolve,
)
from microtonic_calc.scala import mapped_keys, used_degrees

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def main():
    parser = argparse.ArgumentParser(
        description="Calculate n-EDO Scale Tune parameters"
    )
    add_common_args(parser)
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args()

    scale, kbm = load_scale(args)
    p = resolve(args)
    result = compute_scale(
        scale.degrees,
        period=scale.period,
        used=used_degrees(kbm, scale),
        range_neg=p["range_neg"],
        range_pos=p["range_pos"],
        step=p["step"],
        exhaustive=args.optimal,
    )
    if not result["map"]:
        raise SystemExit("error: no notes mapped")

    if args.output == "json":
        print(json.dumps(result))
        return

    label = (
        f"{args.edo}-EDO"
        if args.edo is not None
        else (scale.description or basename(args.scl))
    )
    preset = "custom" if is_custom(args) else args.preset
    data = result["data"]

    print(f"\n=== {label} (preset: {preset}) ===")
    print(f"step: {result['step']}, bias: {result['bias']}")
    print(f"Channels required: {result['channels']}")
    print(f"Ports required: {result['ports']}")
    print(f"Optimal: {'yes' if result['optimal'] else 'no (upper bound)'}\n")

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

    if kbm is not None:
        print()
        by_degree = {d["degree"]: d for d in result["map"]}
        rows = []
        for key, degree, period_index in mapped_keys(kbm, scale):
            entry = by_degree[degree]
            note = entry["semitone"] + 12 * period_index
            rows.append(
                [
                    key,
                    degree,
                    entry["channel"],
                    min(127, max(0, note)),
                ]
            )
        print("Key mapping (key -> degree, channel, note):")
        print(tabulate([["key", "deg", "ch", "note"]] + rows, tablefmt="grid"))


if __name__ == "__main__":
    main()
