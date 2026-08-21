import argparse
import sys

import mido
from microtonic_calc.calc import compute_edo
from microtonic_calc.proxy import MidiProxy
from microtonic_calc.main import PRESETS, _parse_step


def parse_args():
    parser = argparse.ArgumentParser(
        description="Real-time MIDI proxy for n-EDO GS Scale Tuning"
    )
    parser.add_argument("--edo", type=int, help="EDO degree count")
    parser.add_argument(
        "--input-port", default=None, help="Input MIDI port name"
    )
    parser.add_argument(
        "--output-port", default=None, help="Output MIDI port name"
    )
    parser.add_argument("--preset", choices=list(PRESETS), default="gs")
    parser.add_argument("--range-neg", type=float, default=None)
    parser.add_argument("--range-pos", type=float, default=None)
    parser.add_argument("--step", type=_parse_step, default=None)
    parser.add_argument("--max-channels", type=int, default=16)
    parser.add_argument(
        "--list-ports",
        action="store_true",
        help="List available MIDI ports and exit",
    )
    return parser.parse_args()


def list_ports():
    print("Available input ports:")
    for name in mido.get_input_names() or ["(none)"]:
        print(f"  {name}")
    print("Available output ports:")
    for name in mido.get_output_names() or ["(none)"]:
        print(f"  {name}")


def main():
    args = parse_args()

    if args.list_ports:
        list_ports()
        return

    if not args.edo:
        print("Error: --edo is required for proxy mode", file=sys.stderr)
        sys.exit(1)

    p = PRESETS[args.preset]
    range_neg = args.range_neg if args.range_neg is not None else p["range_neg"]
    range_pos = args.range_pos if args.range_pos is not None else p["range_pos"]
    step = args.step if args.step is not None else p["step"]

    result = compute_edo(
        args.edo, range_neg, range_pos, step, args.max_channels
    )

    degree_map = {
        entry["degree"]: {
            "channel": entry["channel"],
            "semitone": entry["semitone"],
        }
        for entry in result["map"]
    }

    proxy = MidiProxy(
        edo=result["edo"],
        tuning_data=result["tuning"]["data"],
        degree_map=degree_map,
        input_port_name=args.input_port,
        output_port_name=args.output_port,
    )

    print(f"Proxying {result['edo']}-EDO GS Scale Tuning", file=sys.stderr)
    print(f"Input:  {args.input_port or '(default)'}", file=sys.stderr)
    print(f"Output: {args.output_port or '(default)'}", file=sys.stderr)
    print(f"Channels: {len(result['tuning']['data'])}", file=sys.stderr)
    print("Press Ctrl+C to stop", file=sys.stderr)
    print("---", file=sys.stderr)

    proxy.run()


if __name__ == "__main__":
    main()
