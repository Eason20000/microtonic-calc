from microtonic_calc.scala import (
    edo_scale,
    parse_kbm,
    parse_scl,
    validate_kbm,
)

PRESETS = {
    "gs": {"range_neg": -64, "range_pos": 63, "step": 1.0},
    "mts-2byte": {"range_neg": -100, "range_pos": 100, "step": 100 / 8192},
}


def parse_step(s):
    if "/" in s:
        a, b = s.split("/")
        return float(a) / float(b)
    return float(s)


def add_common_args(parser, scale_required=True):
    group = parser.add_mutually_exclusive_group(required=scale_required)
    group.add_argument("--edo", type=int, help="EDO degree count")
    group.add_argument("--scl", metavar="FILE", help="Scala scale file")
    parser.add_argument(
        "--kbm", metavar="FILE", help="Scala keyboard mapping (with --scl)"
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
    parser.add_argument(
        "--optimal",
        action="store_true",
        help="exhaustively search for the minimum channel count",
    )


def load_scale(args):
    if args.edo is not None:
        if args.kbm:
            raise SystemExit("error: --kbm requires --scl")
        return edo_scale(args.edo), None

    if args.scl is None:
        raise SystemExit("error: one of --edo or --scl is required")

    try:
        with open(args.scl, encoding="latin-1") as f:
            scale = parse_scl(f.read())
    except (OSError, ValueError) as exc:
        raise SystemExit(f"error: {args.scl}: {exc}") from exc

    if args.kbm is None:
        return scale, None

    try:
        with open(args.kbm, encoding="latin-1") as f:
            kbm = parse_kbm(f.read())
        validate_kbm(kbm, scale)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"error: {args.kbm}: {exc}") from exc

    return scale, kbm


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
