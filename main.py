import argparse
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


def main():
    parser = argparse.ArgumentParser(
        description="Calculate n-EDO Scale Tune parameters"
    )
    parser.add_argument("--edo", type=int, required=True)
    parser.add_argument(
        "--preset", choices=list(PRESETS), default="gs",
        help="Preset: gs (default, -64/+63, step 1) | mts-2byte (-100/+100, step 100/8192)"
    )
    parser.add_argument("--range-neg", type=float, default=None)
    parser.add_argument("--range-pos", type=float, default=None)
    parser.add_argument("--step", type=_parse_step, default=None)
    parser.add_argument("--max-m", type=int, default=16)
    args = parser.parse_args()

    p = PRESETS[args.preset]
    range_neg = args.range_neg if args.range_neg is not None else p["range_neg"]
    range_pos = args.range_pos if args.range_pos is not None else p["range_pos"]
    step = args.step if args.step is not None else p["step"]

    result = compute_edo(args.edo, range_neg, range_pos, step, args.max_m)

    print(f"\n=== {result['n']}-EDO (preset: {args.preset}) ===")
    print(f"Channels required: {result['m']}\n")

    ch_header = [f"ch{c['channel']}" for c in result["channels"]]
    table = [["note"] + ch_header]
    for ni, name in enumerate(NOTE_NAMES):
        row = [name]
        for ch in result["channels"]:
            off = ch["offsets"][ni]
            row.append(str(off) if off is not None else "N/A")
        table.append(row)
    print("Per-channel offsets:")
    gprint(table)
    print()

    header = ["deg", "cents", "ch", "note", "offset", "error"]
    rows = []
    for d in result["degrees"]:
        rows.append([
            d["degree"],
            str(d["cents"]),
            d["channel"],
            d["note_name"],
            str(d["offset"]),
            str(d["error"]),
        ])
    print("Mapping (degree -> channel, note, offset):")
    gprint([header] + rows)

    print(f"Max error: {result['max_error']} cents")


if __name__ == "__main__":
    main()
