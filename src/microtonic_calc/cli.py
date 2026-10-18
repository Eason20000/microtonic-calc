PRESETS = {
    "gs": {"range_neg": -64, "range_pos": 63, "step": 1.0},
    "mts-2byte": {"range_neg": -100, "range_pos": 100, "step": 100 / 8192},
}


def parse_step(s):
    if "/" in s:
        a, b = s.split("/")
        return float(a) / float(b)
    return float(s)


def add_common_args(parser, edo_required=False):
    parser.add_argument(
        "--edo", type=int, required=edo_required, help="EDO degree count"
    )
    parser.add_argument(
        "--preset",
        choices=list(PRESETS),
        default="gs",
        help="gs (default) | mts-2byte",
    )
    parser.add_argument("--range-neg", type=float, default=None)
    parser.add_argument("--range-pos", type=float, default=None)
    parser.add_argument("--step", type=parse_step, default=None)
    parser.add_argument("--max-channels", type=int, default=16)


def resolve(args):
    return {
        "range_neg": _pick(args.range_neg, args.preset, "range_neg"),
        "range_pos": _pick(args.range_pos, args.preset, "range_pos"),
        "step": _pick(args.step, args.preset, "step"),
    }


def _pick(value, preset, key):
    return value if value is not None else PRESETS[preset][key]


def is_custom(args):
    return any(
        getattr(args, name) is not None
        for name in ("range_neg", "range_pos", "step")
    )
