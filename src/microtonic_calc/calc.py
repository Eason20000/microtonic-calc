from math import ceil, floor


def _round_half_up(x):
    return floor(x + 0.5)


def compute_edo(n, range_neg=-64, range_pos=63, step=1.0, max_channels=16):
    bias = _round_half_up(-range_neg / step)
    for channels in range(ceil(n / 12), max_channels + 1):
        result = _assign(n, channels, range_neg, range_pos, step, bias)
        if result is not None:
            return result
    raise RuntimeError(
        f"cannot assign {n}-EDO: range=[{range_neg}, {range_pos}] "
        f"step={step} no valid assignment within {max_channels} channels"
    )


def _assign(n, channels, range_neg, range_pos, step, bias):
    data = [[None] * 12 for _ in range(channels)]
    mapping = []

    for degree in range(n):
        cents = degree * 1200.0 / n
        ch = degree % channels
        for semi in _candidate_semitones(cents):
            value = _round_half_up((cents - semi * 100) / step) + bias
            if not range_neg <= (value - bias) * step <= range_pos:
                continue
            slot = semi % 12
            existing = data[ch][slot]
            if existing is not None and existing != value:
                continue
            data[ch][slot] = value
            mapping.append({"degree": degree, "channel": ch, "semitone": semi})
            break
        else:
            return None

    return {"edo": n, "step": step, "bias": bias, "data": data, "map": mapping}


def _candidate_semitones(cents):
    t_floor = floor(cents / 100)
    t_round = _round_half_up(cents / 100)
    yield t_floor
    if t_round != t_floor:
        yield t_round
