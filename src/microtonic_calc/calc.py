from math import ceil, floor


def _round_half_up(x):
    return floor(x + 0.5)


def _quantize(value, step):
    return _round_half_up(value / step) * step


def _cents_to_value(cents, step, bias):
    return _round_half_up(cents / step) + bias


def compute_edo(n, range_neg=-64, range_pos=63, step=1.0, max_channels=16):
    bias = _round_half_up(-range_neg / step)
    channels = ceil(n / 12)
    while channels <= max_channels:
        result = _try_assign(n, channels, range_neg, range_pos, step, bias)
        if result is not None:
            return result
        channels += 1
    raise RuntimeError(
        f"cannot assign {n}-EDO: "
        f"range=[{range_neg}, {range_pos}] step={step} "
        f"no valid assignment within {max_channels} channels"
    )


def _try_assign(n, num_channels, range_neg, range_pos, step, bias):
    channel_data = [{"channel": ch, "offsets": [None] * 12} for ch in range(num_channels)]
    map_entries = []

    for i in range(n):
        cents = i * 1200.0 / n
        ch = i % num_channels

        t_floor = floor(cents / 100)
        off_floor = _quantize(cents - t_floor * 100, step)

        t_round = _round_half_up(cents / 100)
        off_round = _quantize(cents - t_round * 100, step) if t_round != t_floor else None

        candidates = []
        if range_neg <= off_floor <= range_pos:
            candidates.append((t_floor, off_floor))
        if off_round is not None and range_neg <= off_round <= range_pos:
            candidates.append((t_round, off_round))

        assigned = False
        for target_semi, offset in candidates:
            note_in_oct = target_semi % 12
            value = _cents_to_value(offset, step, bias)
            existing = channel_data[ch]["offsets"][note_in_oct]
            if existing is not None and existing != value:
                continue
            if existing is None:
                channel_data[ch]["offsets"][note_in_oct] = value
            map_entries.append({
                "degree": i,
                "channel": ch,
                "semitone": note_in_oct,
                "value": value,
            })
            assigned = True
            break

        if not assigned:
            return None

    return {
        "edo": n,
        "tuning": {
            "step": step,
            "bias": bias,
            "data": channel_data,
        },
        "map": map_entries,
    }
