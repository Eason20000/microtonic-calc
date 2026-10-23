# microtonic-calc

n-EDO / Scala scale tune parameter calculator for MIDI devices.

## Run

```bash
nix run . --option builders '' -- --edo 53
nix run . --option builders '' -- --scl scale.scl --kbm map.kbm
python -m microtonic_calc.main --edo 53
```

## CLI

`mtcalc`:

```
--edo N | --scl FILE     # exactly one scale source
--kbm FILE               # optional, only with --scl
--preset {gs,mts-2byte}  # default: gs
--range-neg F            # override preset
--range-pos F            # override preset
--step F|A/B             # override preset (supports fractions, e.g. 100/8192)
--optimal                # exhaustive search for the minimum channel count
--output {text,json}     # default text
```

`mtproxy` adds:

```
-l, --list-ports         # list indexed ports and exit
-i, --input-port N       # input port index (default 0)
-p, --output-port I,J    # comma-separated output port indices
--key-offset N           # transpose input notes
```

## Architecture

| File                             | Role                                                                          |
| -------------------------------- | ----------------------------------------------------------------------------- |
| `src/microtonic_calc/scala.py`   | `.scl`/`.kbm` parsing, `Scale`/`KeyboardMap`, key→degree mapping helpers.     |
| `src/microtonic_calc/calc.py`    | Pure computation. `compute_scale(...)` → dict. No I/O, no project imports.    |
| `src/microtonic_calc/cli.py`     | Shared CLI helpers: `PRESETS`, `parse_step`, `add_common_args`, `load_scale`. |
| `src/microtonic_calc/main.py`    | `mtcalc` CLI: argument parsing and table display.                             |
| `src/microtonic_calc/mtproxy.py` | `mtproxy` CLI: real-time MIDI proxy + GS Scale Tuning SysEx builder.          |

## Data contract

`calc.py` returns

```
{degrees, period, step, bias, channels, ports, data, map, optimal}
```

- `degrees` — cents of each degree within one period; `degrees[0] == 0.0`
- `period` — must be 1200 (octave-repeating scales only)
- `channels` — global part count; `ports = ceil(channels / 16)`
- `optimal` — true when `channels` is proven minimal
- `data[channel][slot]` — raw integers (bias + cents/step), ready to send
- `map[].semitone` — absolute semitone; the channel's `data[channel]` slot is
  `semitone % 12`
- Convert to cents: `(value - bias) * step`

## Rounding

**Never use Python's `round()`.** All rounding uses
`_round_half_up = floor(x + 0.5)`:

- `_round_half_up((cents - semi * 100) / step) + bias` — round cents to an
  integer tuning value
- A degree's candidates are **all** semitones whose offset lies in
  `[range_neg, range_pos]`; `t_floor` and `t_round` are ordered first, then the
  rest by absolute offset (for the greedy pass)

## Presets

| Name           | range_neg | range_pos | step     |
| -------------- | --------- | --------- | -------- |
| `gs` (default) | -64       | +63       | 1.0      |
| `mts-2byte`    | -100      | +100      | 100/8192 |

Explicit `--range-neg`/`--range-pos`/`--step` override the preset. Display label
shows `custom` when any override is active.

## Channel assignment

- Each degree has a candidate list: every semitone with offset in
  `[range_neg, range_pos]`, ordered floor-first then by absolute offset.
- The greedy pass takes the first candidate, groups by slot (`semitone % 12`)
  and ranks distinct values; this is an upper bound.
- A lower bound comes from forced values (single-option degrees) plus a
  pigeonhole bound over 1–3 slot subsets (only when no value sharing is possible
  in the subset).
- If `upper == lower`, the result is proven optimal.
- Otherwise a depth-first branch-and-bound searches for a better assignment
  (default 200k nodes; `--optimal` removes the budget). `optimal` is true only
  when minimality is proven.
- `channels = max(distinct values per slot)`; global channel `c` maps to port
  `c // 16`, local part `c % 16`.

## Scales

- `.scl` — implicit `1/1` (0 cents) is degree 0; the last pitch value is the
  period. Period must be 1200; non-octave scales are rejected.
- `.kbm` — `size`, `first`, `last`, `middle`, `reference_note`,
  `reference_frequency`, `formal_octave`, then `size` mapping entries (`x` =
  unmapped). Only `formal_octave` equal to the scale size (or `0`) and mapping
  entries below the scale size are supported.
- The reference note/frequency are ignored (GS Scale Tuning has no master
  tuning).
- Without `--kbm`, an identity/cyclic mapping is used: key → degree `key % k`,
  period `key // k`.
- Key mapping: `degree = mapping[(key - middle) % size]`,
  `period = (key - middle) // size`; output note = `semitone + 12 * period`.

## MIDI proxy

- Ports are addressed by 0-based indices from `-l`; indices are a snapshot of
  the current device list.
- If `-p` is omitted, the first `ports` output indices are selected; if there
  are not enough ports, the proxy exits with an error.
- Unmapped or out-of-range input keys are dropped; output notes are clamped to
  `0..127`.
- SysEx is sent only for used parts. Each port receives its own parts.

## Commit style

Conventional commits (`fix:`, `feat:`, `refactor:`, etc.).

## Tests

None configured.
