from mido import Message, open_input, open_output

from microtonic_calc.gs_sysex import build_gs_scale_tuning_sysex


class MidiProxy:
    def __init__(
        self, edo, tuning_data, degree_map, input_port_name, output_port_name
    ):
        self.edo = edo
        self.tuning_data = tuning_data
        self.degree_map = degree_map
        self.inport = open_input(input_port_name)
        self.outport = open_output(output_port_name)

    def send_tuning(self):
        for ch_data in self.tuning_data:
            offsets = ch_data["offsets"]
            msg = build_gs_scale_tuning_sysex(ch_data["channel"], offsets)
            self.outport.send(msg)

    def run(self):
        self.send_tuning()
        try:
            for msg in self.inport:
                if msg.type not in ("note_on", "note_off"):
                    continue
                octave, degree = divmod(msg.note, self.edo)
                channel = self.degree_map[degree]["channel"]
                note = self.degree_map[degree]["semitone"] + 12 * octave
                self.outport.send(msg.copy(channel=channel, note=note))
        except KeyboardInterrupt:
            pass
        finally:
            self.inport.close()
            self.outport.close()
