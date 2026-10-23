import argparse
import sys

import mido
from mido import Message, open_input, open_output

from microtonic_calc.calc import PARTS_PER_PORT, compute_scale
from microtonic_calc.cli import add_common_args, load_scale, resolve
from microtonic_calc.scala import mapped_keys, used_degrees

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


def _parse_indices(text):
    try:
        return [int(part) for part in text.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "expected comma-separated integers, e.g. 0,1"
        ) from exc


def list_ports():
    print("input:")
    for index, name in enumerate(mido.get_input_names()):
        print(f"  {index}  {name}")
    print("output:")
    for index, name in enumerate(mido.get_output_names()):
        print(f"  {index}  {name}")


def _pick_input(index):
    names = mido.get_input_names()
    if not names:
        raise SystemExit("error: no MIDI input ports available")
    if not 0 <= index < len(names):
        raise SystemExit(
            f"error: input port index {index} out of range "
            f"(0..{len(names) - 1}); use -l to list ports"
        )
    return names[index]


def _pick_outputs(indices, required):
    names = mido.get_output_names()
    if not names:
        raise SystemExit("error: no MIDI output ports available")
    if indices is None:
        if len(names) < required:
            raise SystemExit(
                f"error: {required} output port(s) required but only "
                f"{len(names)} available; use -l and -p"
            )
        return names[:required]

    if len(set(indices)) != len(indices):
        raise SystemExit("error: duplicate output port indices")
    if len(indices) < required:
        raise SystemExit(
            f"error: {required} output port(s) required but "
            f"{len(indices)} provided; use -l and -p"
        )
    for index in indices:
        if not 0 <= index < len(names):
            raise SystemExit(
                f"error: output port index {index} out of range "
                f"(0..{len(names) - 1}); use -l to list ports"
            )
    return [names[index] for index in indices[:required]]


def build_table(scale, kbm, result):
    by_degree = {d["degree"]: d for d in result["map"]}
    table = {}
    for key, degree, period_index in mapped_keys(kbm, scale):
        entry = by_degree[degree]
        note = entry["semitone"] + 12 * period_index
        table[key] = (entry["channel"], min(127, max(0, note)))
    return table


class MidiProxy:
    def __init__(self, data, table, output_ports, input_port, key_offset):
        self.data = data
        self.table = table
        self.output_ports = output_ports
        self.input_port = input_port
        self.key_offset = key_offset

    def send_tuning(self):
        for channel, offsets in enumerate(self.data):
            port, local = divmod(channel, PARTS_PER_PORT)
            self.output_ports[port].send(
                build_gs_scale_tuning_sysex(local, offsets)
            )

    def run(self):
        self.send_tuning()
        try:
            for msg in self.input_port:
                if msg.type not in ("note_on", "note_off"):
                    continue
                target = self.table.get(msg.note + self.key_offset)
                if target is None:
                    continue
                channel, note = target
                port, local = divmod(channel, PARTS_PER_PORT)
                self.output_ports[port].send(msg.copy(channel=local, note=note))
        except KeyboardInterrupt:
            pass
        finally:
            self.input_port.close()
            for port in self.output_ports:
                port.close()


def main():
    parser = argparse.ArgumentParser(
        description="Real-time MIDI proxy for n-EDO GS Scale Tuning"
    )
    add_common_args(parser, scale_required=False)
    parser.add_argument(
        "-l", "--list-ports", action="store_true", help="list ports and exit"
    )
    parser.add_argument(
        "-i", "--input-port", type=int, default=0, help="input port index"
    )
    parser.add_argument(
        "-p",
        "--output-port",
        type=_parse_indices,
        default=None,
        help="comma-separated output port indices, e.g. 1,2",
    )
    parser.add_argument("--key-offset", type=int, default=0)
    args = parser.parse_args()

    if args.list_ports:
        list_ports()
        return

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

    table = build_table(scale, kbm, result)
    input_name = _pick_input(args.input_port)
    output_names = _pick_outputs(args.output_port, result["ports"])

    try:
        input_port = open_input(input_name)
    except OSError as exc:
        raise SystemExit(
            f"error: cannot open input {input_name!r}: {exc}"
        ) from exc

    output_ports = []
    try:
        for name in output_names:
            output_ports.append(open_output(name))
    except OSError as exc:
        input_port.close()
        for port in output_ports:
            port.close()
        raise SystemExit(f"error: cannot open output {name!r}: {exc}") from exc

    print(
        f"Proxying {result['channels']} channel(s) across "
        f"{result['ports']} port(s)",
        file=sys.stderr,
    )
    print(f"Input:  {args.input_port} {input_name}", file=sys.stderr)
    indices = args.output_port or list(range(len(output_names)))
    for index, name in zip(indices, output_names):
        print(f"Output: {index} {name}", file=sys.stderr)
    print("Press Ctrl+C to stop", file=sys.stderr)
    print("---", file=sys.stderr)

    MidiProxy(
        result["data"],
        table,
        output_ports,
        input_port,
        args.key_offset,
    ).run()


if __name__ == "__main__":
    main()
