# microtonic-calc

n-EDO / Scala scale tune parameter calculator for MIDI devices.

## Usage

Install and use the `mtcalc` command:

```bash
pip install . && mtcalc --help
```

Or run directly from source without installing:

```bash
python -m microtonic_calc.main --help
```

Or run via Nix:

```bash
nix run . -- --help
```

Scales can be given as an EDO count or as Scala `.scl` (optionally with `.kbm`):

```bash
mtcalc --edo 53
mtcalc --scl scale.scl
mtcalc --scl scale.scl --kbm map.kbm
```

Only octave-repeating scales (period = 1200 cents) are supported.

For the MIDI proxy:

```bash
nix shell . -c mtproxy -- --edo 53
```

## CLI

| Flag                      | Description                                                |
| ------------------------- | ---------------------------------------------------------- |
| `--edo N`                 | EDO degree count (exactly one of `--edo`/`--scl`)          |
| `--scl FILE`              | Scala scale file                                           |
| `--kbm FILE`              | Scala keyboard mapping (only with `--scl`)                 |
| `--preset {gs,mts-2byte}` | Preset (default `gs`)                                      |
| `--range-neg F`           | Override preset negative range                             |
| `--range-pos F`           | Override preset positive range                             |
| `--step F\|A/B`           | Override preset step (supports fractions, e.g. `100/8192`) |
| `--optimal`               | Exhaustively search for the minimum channel count          |
| `--output {text,json}`    | Output format (default `text`)                             |

By default the calculator proves optimality when it can and otherwise runs a
bounded search (200k nodes). `--optimal` removes that budget. JSON output
includes an `optimal` flag indicating whether the channel count is proven
minimal.

## MIDI Proxy

The `mtproxy` command runs a real-time MIDI proxy that applies n-EDO GS Scale
Tuning.

```bash
mtproxy -l                              # list indexed ports
mtproxy --edo 53 -i 0 -p 1              # input 0, output 1
mtproxy --scl scale.scl --kbm map.kbm -p 1,2
```

| Flag                      | Description                                   |
| ------------------------- | --------------------------------------------- |
| `-l`, `--list-ports`      | List indexed input/output ports and exit      |
| `-i`, `--input-port N`    | Input port index (default 0)                  |
| `-p`, `--output-port I,J` | Comma-separated output port indices           |
| `--edo N`                 | EDO degree count (exactly one of --edo/--scl) |
| `--scl FILE`              | Scala scale file                              |
| `--kbm FILE`              | Scala keyboard mapping (only with `--scl`)    |
| `--preset {gs,mts-2byte}` | Preset (default `gs`)                         |
| `--optimal`               | Exhaustively search for minimum channels      |
| `--key-offset N`          | Transpose input notes (default 0)             |

When `-p` is omitted, the first `ceil(channels / 16)` output ports are used; if
there are not enough ports the proxy exits with an error. Each port hosts 16
parts, so dense scales can span multiple ports. Input keys that are unmapped or
outside the MIDI range are dropped; output notes are clamped to `0..127`.

## Presets

| Preset      | range_neg | range_pos | step     |
| ----------- | --------- | --------- | -------- |
| `gs`        | -64       | +63       | 1.0      |
| `mts-2byte` | -100      | +100      | 100/8192 |

## License

GNU General Public License v3.0
