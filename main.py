import argparse
import json
from tabulate import tabulate
from calc import compute_edo, NOTE_NAMES

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


def _sysex_to_cents(val, step, bias):
    return (val - bias) * step


def main():
    parser = argparse.ArgumentParser(
        description="Calculate n-EDO Scale Tune parameters"
    )
    parser.add_argument("--edo", type=int, required=True)
    parser.add_argument(
        "--preset", choices=list(PRESETS), default="gs",
        help="gs (default, -64/+63, step 1) | mts-2byte (-100/+100, step 100/8192)"
    )
    parser.add_argument("--range-neg", type=float, default=None)
    parser.add_argument("--range-pos", type=float, default=None)
    parser.add_argument("--step", type=_parse_step, default=None)
    parser.add_argument("--max-m", type=int, default=16)
    parser.add_argument(
        "--output", choices=["text", "json"], default="text"
    )
    args = parser.parse_args()

    p = PRESETS[args.preset]
    overridden = args.range_neg is not None or args.range_pos is not None or args.step is not None
    range_neg = args.range_neg if args.range_neg is not None else p["range_neg"]
    range_pos = args.range_pos if args.range_pos is not None else p["range_pos"]
    step = args.step if args.step is not None else p["step"]

    result = compute_edo(args.edo, range_neg, range_pos, step, args.max_m)

    if args.output == "json":
        print(json.dumps(result))
        return

    label = "custom" if overridden else args.preset

    sysex = result["sysex"]
    bias = sysex["bias"]
    channel_count = len(sysex["data"])

    print(f"\n=== {result['edo']}-EDO (preset: {label}) ===")
    print(f"Channels required: {channel_count}\n")

    ch_header = [f"ch{c['channel']}" for c in sysex["data"]]
    table = [["note"] + ch_header]
    for ni, name in enumerate(NOTE_NAMES):
        row = [name]
        for ch in sysex["data"]:
            v = ch["offsets"][ni]
            row.append(str(_sysex_to_cents(v, step, bias)) if v is not None else "N/A")
        table.append(row)
    print("Per-channel offsets:")
    gprint(table)
    print()

    header = ["deg", "cents", "ch", "note", "offset", "error"]
    rows = []
    max_error = 0.0
    for d in result["map"]:
        cents = d["degree"] * 1200.0 / result["edo"]
        offset_cents = _sysex_to_cents(d["sysex_value"], step, bias)
        target_semi = int(cents / 100 + 0.5) if offset_cents < 0 else int(cents / 100)
        error = cents - (target_semi * 100 + offset_cents)
        max_error = max(max_error, abs(error))
        rows.append([
            d["degree"],
            str(cents),
            d["channel"],
            d["note_name"],
            str(offset_cents),
            str(error),
        ])
    print("Mapping (degree -> channel, note, offset):")
    gprint([header] + rows)

    print(f"Max error: {max_error} cents")


if __name__ == "__main__":
    main()
