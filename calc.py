from math import ceil

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _quantize(value, step):
    return round(value / step) * step


def compute_edo(n, range_neg=-64, range_pos=63, step=1.0, max_m=16):
    m = ceil(n / 12)
    while m <= max_m:
        result = _try_assign(n, m, range_neg, range_pos, step)
        if result is not None:
            return result
        m += 1
    raise RuntimeError(
        f"cannot assign {n}-EDO: "
        f"range=[{range_neg}, {range_pos}] step={step} "
        f"no valid assignment within {max_m} channels"
    )


def _try_assign(n, m, range_neg, range_pos, step):
    channels = [{"channel": ch, "offsets": [None] * 12} for ch in range(m)]
    degrees = []

    for i in range(n):
        cents = i * 1200.0 / n
        ch = i % m

        t_floor = int(cents / 100)
        off_floor = _quantize(cents - t_floor * 100, step)

        t_ceil = int(cents / 100 + 0.5)
        off_ceil = _quantize(cents - t_ceil * 100, step) if t_ceil != t_floor else None

        candidates = []
        if range_neg <= off_floor <= range_pos:
            candidates.append((t_floor, off_floor))
        if off_ceil is not None and range_neg <= off_ceil <= range_pos:
            candidates.append((t_ceil, off_ceil))

        assigned = False
        for target_semi, offset in candidates:
            note_in_oct = target_semi % 12
            existing = channels[ch]["offsets"][note_in_oct]
            if existing is not None and existing != offset:
                continue
            if existing is None:
                channels[ch]["offsets"][note_in_oct] = offset
            error = cents - (target_semi * 100 + offset)
            degrees.append({
                "degree": i,
                "cents": cents,
                "channel": ch,
                "note_name": NOTE_NAMES[note_in_oct],
                "offset": offset,
                "error": error,
            })
            assigned = True
            break

        if not assigned:
            return None

    max_error = max(abs(d["error"]) for d in degrees) if degrees else 0

    return {
        "n": n,
        "m": m,
        "channels": channels,
        "degrees": degrees,
        "max_error": max_error,
    }
