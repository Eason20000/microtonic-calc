# microtonic-calc

n-EDO Scale Tune SysEx parameter calculator for MIDI devices.

## Usage

```bash
python -m main --help
```

Or via Nix:

```bash
nix run . -- --help
```

## CLI

| Flag | Description |
|---|---|
| `--edo N` | EDO degree count (required) |
| `--preset {gs,mts-2byte}` | Preset (default `gs`) |
| `--range-neg F` | Override preset negative range |
| `--range-pos F` | Override preset positive range |
| `--step F\|A/B` | Override preset step (supports fractions, e.g. `100/8192`) |
| `--max-channels N` | Max channels (default 16) |
| `--output {text,json}` | Output format (default `text`) |

## Presets

| Preset | range_neg | range_pos | step |
|---|---|---|---|
| `gs` | -64 | +63 | 1.0 |
| `mts-2byte` | -100 | +100 | 100/8192 |

## License

GNU General Public License v3.0
