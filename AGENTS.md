# microtonic-calc

n-EDO Scale Tune parameter calculator for MIDI devices.

## Run

```bash
nix run . --option builders '' -- --edo 53
python -m microtonic_calc.main --edo 53
```

## CLI

```
--edo N          # required
--preset {gs,mts-2byte}  # default: gs
--range-neg F    # override preset
--range-pos F    # override preset
--step F|A/B     # override preset (supports fraction, e.g. 100/8192)
--max-channels N  # default 16
--output {text,json}  # default text
```

## Architecture

| File                             | Role                                                                       |
| -------------------------------- | -------------------------------------------------------------------------- |
| `src/microtonic_calc/calc.py`    | Pure computation. `compute_edo(...)` → dict. No I/O, no project imports.   |
| `src/microtonic_calc/cli.py`     | Shared CLI helpers: `PRESETS`, `parse_step`, `add_common_args`, `resolve`. |
| `src/microtonic_calc/main.py`    | `mtcalc` CLI: argument parsing and table display.                          |
| `src/microtonic_calc/mtproxy.py` | `mtproxy` CLI: real-time MIDI proxy core + GS Scale Tuning SysEx builder.  |

## Data contract

`src/microtonic_calc/calc.py` returns
`{edo, step, bias, data: [[12 x int_or_None] per channel], map: [{degree, channel, semitone}]}`.

- `data[channel][slot]` are raw integers (bias + cents/step), ready to send to
  device
- `map[].semitone` is the absolute semitone within the EDO octave; the channel's
  `data[channel]` slot is `semitone % 12`
- Convert to cents: `(value - bias) * step`

## Rounding

**Never use Python's `round()`.** All rounding uses
`_round_half_up = floor(x + 0.5)`:

- `_round_half_up((cents - semi * 100) / step) + bias` — round cents to an
  integer tuning value
- `t_floor` (`floor(cents/100)`) vs `t_round` (`_round_half_up(cents/100)`) —
  two candidate semitone assignments per degree

## Presets

| Name           | range_neg | range_pos | step     |
| -------------- | --------- | --------- | -------- |
| `gs` (default) | -64       | +63       | 1.0      |
| `mts-2byte`    | -100      | +100      | 100/8192 |

Explicit `--range-neg`/`--range-pos`/`--step` override the preset. Display label
shows `custom` when any override is active.

## Slot assignment

- Degrees are interleaved across channels: `i % channels`
- `t_floor` candidate preferred (keeps note in same octave); fallback to
  `t_round`
- If two degrees share a slot with the same value, they share successfully
- If no candidate fits, channels is incremented up to `--max-channels` (default
  16\)
- `channels` is the result of the search, not pre-computed as `ceil(n/12)`

## Commit style

Conventional commits (`fix:`, `feat:`, `refactor:`, etc.).

## Tests

None configured.
