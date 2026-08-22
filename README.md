# microtonic-calc

n-EDO Scale Tune SysEx parameter calculator for MIDI devices.

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

For the MIDI proxy:

```bash
nix shell . -c mtproxy -- --edo 53
```

## CLI

| Flag                      | Description                                                |
| ------------------------- | ---------------------------------------------------------- |
| `--edo N`                 | EDO degree count (required)                                |
| `--preset {gs,mts-2byte}` | Preset (default `gs`)                                      |
| `--range-neg F`           | Override preset negative range                             |
| `--range-pos F`           | Override preset positive range                             |
| `--step F\|A/B`           | Override preset step (supports fractions, e.g. `100/8192`) |
| `--max-channels N`        | Max channels (default 16)                                  |
| `--output {text,json}`    | Output format (default `text`)                             |

## MIDI Proxy

The `mtproxy` command runs a real-time MIDI proxy that applies n-EDO GS Scale
Tuning.

```bash
mtproxy --edo 53 --input-port "MIDI In" --output-port "MIDI Out"
```

| Flag                      | Description                        |
| ------------------------- | ---------------------------------- |
| `--edo N`                 | EDO degree count (required)        |
| `--input-port NAME`       | Input MIDI port (default: system)  |
| `--output-port NAME`      | Output MIDI port (default: system) |
| `--preset {gs,mts-2byte}` | Preset (default `gs`)              |
| `--key-offset N`          | Transpose input notes (default 0)  |
| `--list-ports`            | List available MIDI ports and exit |

## Presets

| Preset      | range_neg | range_pos | step     |
| ----------- | --------- | --------- | -------- |
| `gs`        | -64       | +63       | 1.0      |
| `mts-2byte` | -100      | +100      | 100/8192 |

## License

GNU General Public License v3.0
