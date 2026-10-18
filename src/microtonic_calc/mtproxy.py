import argparse
import sys

import mido
from mido import Message, open_input, open_output

from microtonic_calc.calc import compute_edo
from microtonic_calc.cli import add_common_args, resolve

ROLAND_ID = (0x41, 0x10)
GS_MODEL = 0x42
DEVICE_ID = 0x12
PARAM_ADDR = 0x40
FIXED_BYTE = 0x40


def build_gs_scale_tuning_sysex(channel, offsets):
    addr = [PARAM_ADDR, 0x11 + channel, FIXED_BYTE]
    filled = [o if o is not None else 64 for o in offsets]
    checksum = (128 - sum(addr + filled) % 128) & 127
    data = list(ROLAND_ID) + [GS_MODEL, DEVICE_ID] + addr + filled + [checksum]
    return Message("sysex", data=tuple(data))


def map_note(edo, degree_map, key_offset, note):
    octave, degree = divmod(note + key_offset, edo)
    channel, semitone = degree_map[degree]
    return channel, min(127, max(0, semitone + 12 * octave))


class MidiProxy:
    def __init__(
        self, edo, data, degree_map, input_port, output_port, key_offset
    ):
        self.edo = edo
        self.data = data
        self.degree_map = degree_map
        self.key_offset = key_offset
        self.inport = open_input(input_port)
        self.outport = open_output(output_port)

    def send_tuning(self):
        for channel, offsets in enumerate(self.data):
            self.outport.send(build_gs_scale_tuning_sysex(channel, offsets))

    def run(self):
        self.send_tuning()
        try:
            for msg in self.inport:
                if msg.type not in ("note_on", "note_off"):
                    continue
                channel, note = map_note(
                    self.edo, self.degree_map, self.key_offset, msg.note
                )
                self.outport.send(msg.copy(channel=channel, note=note))
        except KeyboardInterrupt:
            pass
        finally:
            self.inport.close()
            self.outport.close()


def list_ports():
    print("Available input ports:")
    for name in mido.get_input_names() or ["(none)"]:
        print(f"  {name}")
    print("Available output ports:")
    for name in mido.get_output_names() or ["(none)"]:
        print(f"  {name}")


def main():
    parser = argparse.ArgumentParser(
        description="Real-time MIDI proxy for n-EDO GS Scale Tuning"
    )
    add_common_args(parser)
    parser.add_argument("--input-port", default=None, help="Input MIDI port")
    parser.add_argument("--output-port", default=None, help="Output MIDI port")
    parser.add_argument("--key-offset", type=int, default=0)
    parser.add_argument(
        "--list-ports",
        action="store_true",
        help="List available MIDI ports and exit",
    )
    args = parser.parse_args()

    if args.list_ports:
        list_ports()
        return

    if not args.edo:
        print("Error: --edo is required for proxy mode", file=sys.stderr)
        sys.exit(1)

    p = resolve(args)
    result = compute_edo(
        args.edo, p["range_neg"], p["range_pos"], p["step"], args.max_channels
    )
    degree_map = {
        d["degree"]: (d["channel"], d["semitone"]) for d in result["map"]
    }

    proxy = MidiProxy(
        edo=result["edo"],
        data=result["data"],
        degree_map=degree_map,
        input_port=args.input_port,
        output_port=args.output_port,
        key_offset=args.key_offset,
    )

    print(f"Proxying {result['edo']}-EDO GS Scale Tuning", file=sys.stderr)
    print(f"Input:  {args.input_port or '(default)'}", file=sys.stderr)
    print(f"Output: {args.output_port or '(default)'}", file=sys.stderr)
    print(f"Channels: {len(result['data'])}", file=sys.stderr)
    print("Press Ctrl+C to stop", file=sys.stderr)
    print("---", file=sys.stderr)

    proxy.run()


if __name__ == "__main__":
    main()
