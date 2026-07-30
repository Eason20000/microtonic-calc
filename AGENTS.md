# microtonic-calc

n-EDO Scale Tune parameter calculator for MIDI devices.

## Run

```bash
nix run . --option builders '' -- --edo 53
python -m src.main --edo 53
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

| File | Role |
|---|---|
| `src/calc.py` | Pure computation. `compute_edo(n, range_neg, range_pos, step, max_channels)` → dict. No I/O. |
| `src/main.py` | CLI arg parsing, preset resolution, display. Derives `channel_count`, `max_error` itself. |

## Data contract

`src/calc.py` returns `{edo, sysex: {step, bias, data: [{channel, offsets: [12 x int_or_None}]}, map: [{degree, channel, semitone, sysex_value}]}`.

- `sysex.data[].offsets[]` are raw integers (bias + cents/step), ready to send to device
- `map[].sysex_value` matches the channel's offset for that degree
- Convert to cents: `(value - bias) * step`

## Rounding

**Never use Python's `round()`.** All rounding uses `_round_half_up = floor(x + 0.5)`:

- `_quantize(value, step)` — truncate cents to nearest step
- `_cents_to_sysex(cents, step, bias)` — round cents to integer sysex value
- `t_round` (half-up) vs `t_floor` — two candidate semitone assignments per degree

## Presets

| Name | range_neg | range_pos | step |
|---|---|---|---|
| `gs` (default) | -64 | +63 | 1.0 |
| `mts-2byte` | -100 | +100 | 100/8192 |

Explicit `--range-neg`/`--range-pos`/`--step` override the preset. Display label shows `custom` when any override is active.

## Slot assignment

- Degrees are interleaved across channels: `i % channels`
- `t_floor` candidate preferred (keeps note in same octave); fallback to `t_round`
- If two degrees share a slot with the same quantized sysex value, they share successfully
- If no candidate fits, channels is incremented up to `--max-channels` (default 16)
- `channels` is the result of the search, not pre-computed as `ceil(n/12)`

## Commit style

Conventional commits (`fix:`, `feat:`, `refactor:`, etc.).

## Tests

None configured.
