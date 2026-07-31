import argparse
import json
from tabulate import tabulate
from microtonic_calc.calc import compute_edo

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

PRESETS = {
    "gs": {"range_neg": -64, "range_pos": 63, "step": 1.0},
    "mts-2byte": {"range_neg": -100, "range_pos": 100, "step": 100 / 8192},
}


def _parse_step(s):
    if "/" in s:
        a, b = s.split("/")
        return float(a) / float(b)
    return float(s)


def gprint(table):
    print(tabulate(table, tablefmt="grid"))


def main():
    parser = argparse.ArgumentParser(
        description="Calculate n-EDO Scale Tune parameters"
    )
    parser.add_argument("--edo", type=int, required=True)
    parser.add_argument(
        "--preset",
        choices=list(PRESETS),
        default="gs",
        help="gs (default, -64/+63, step 1) | mts-2byte (-100/+100, step 100/8192)",
    )
    parser.add_argument("--range-neg", type=float, default=None)
    parser.add_argument("--range-pos", type=float, default=None)
    parser.add_argument("--step", type=_parse_step, default=None)
    parser.add_argument("--max-channels", type=int, default=16)
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args()

    p = PRESETS[args.preset]
    overridden = (
        args.range_neg is not None
        or args.range_pos is not None
        or args.step is not None
    )
    range_neg = args.range_neg if args.range_neg is not None else p["range_neg"]
    range_pos = args.range_pos if args.range_pos is not None else p["range_pos"]
    step = args.step if args.step is not None else p["step"]

    result = compute_edo(
        args.edo, range_neg, range_pos, step, args.max_channels
    )

    if args.output == "json":
        print(json.dumps(result))
        return

    label = "custom" if overridden else args.preset

    tuning = result["tuning"]

    print(f"\n=== {result['edo']}-EDO (preset: {label}) ===")
    print(f"step: {tuning['step']}, bias: {tuning['bias']}")
    print(f"Channels required: {len(tuning['data'])}\n")

    ch_header = [f"ch{c['channel']}" for c in tuning["data"]]
    table = [["note"] + ch_header]
    for ni, name in enumerate(NOTE_NAMES):
        row = [name]
        for ch in tuning["data"]:
            v = ch["offsets"][ni]
            row.append(str(v) if v is not None else "N/A")
        table.append(row)
    print("Per-channel offsets:")
    gprint(table)
    print()

    header = ["deg", "ch", "semitone"]
    rows = [[d["degree"], d["channel"], d["semitone"]] for d in result["map"]]
    print("Mapping (degree -> channel, semitone):")
    gprint([header] + rows)


if __name__ == "__main__":
    main()
