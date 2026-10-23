from dataclasses import dataclass
from itertools import pairwise
from math import log2

OCTAVE = 1200.0


@dataclass
class Scale:
    degrees: list[float]
    period: float = OCTAVE
    description: str = ""


@dataclass
class KeyboardMap:
    size: int
    first: int
    last: int
    middle: int
    reference_note: int
    reference_frequency: float
    formal_octave: int
    mapping: list[int | None]


def edo_scale(n):
    return Scale([OCTAVE * i / n for i in range(n)], OCTAVE, f"{n}-EDO")


def parse_scl(text):
    lines = [
        line.strip()
        for line in text.splitlines()
        if not line.lstrip().startswith("!")
    ]
    if len(lines) < 2:
        raise ValueError("invalid .scl: missing description or note count")
    description = lines[0]
    try:
        count = int(lines[1].split()[0])
    except (IndexError, ValueError) as exc:
        raise ValueError("invalid .scl: bad note count") from exc
    if count <= 0:
        raise ValueError("invalid .scl: note count must be positive")

    pitches = []
    for line in lines[2:]:
        if len(pitches) == count:
            break
        pitches.append(_parse_pitch(line))
    if len(pitches) != count:
        raise ValueError("invalid .scl: not enough pitch values")

    period = pitches[-1]
    if abs(period - OCTAVE) > 1e-6:
        raise ValueError(
            f"non-octave scale not supported (period={period:.6f} cents)"
        )

    degrees = [0.0] + pitches[:-1]
    if any(b <= a for a, b in pairwise(degrees)):
        raise ValueError("invalid .scl: degrees must strictly increase")
    if degrees[-1] >= period:
        raise ValueError("invalid .scl: degree must be below the period")
    return Scale(degrees, period, description)


def _parse_pitch(line):
    tokens = line.split()
    if not tokens:
        raise ValueError("invalid .scl: empty pitch value")
    token = tokens[0]
    if "." in token:
        return float(token)
    if "/" in token:
        num, den = token.split("/", 1)
        num, den = int(num), int(den)
        if num <= 0 or den <= 0:
            raise ValueError(f"invalid .scl ratio {token!r}")
        return OCTAVE * log2(num / den)
    value = int(token)
    if value <= 0:
        raise ValueError(f"invalid .scl ratio {token!r}")
    return OCTAVE * log2(value)


def parse_kbm(text):
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("!")
    ]
    if len(lines) < 7:
        raise ValueError("invalid .kbm: missing header fields")
    try:
        size = int(lines[0].split()[0])
        first = int(lines[1].split()[0])
        last = int(lines[2].split()[0])
        middle = int(lines[3].split()[0])
        reference_note = int(lines[4].split()[0])
        reference_frequency = float(lines[5].split()[0])
        formal_octave = int(lines[6].split()[0])
    except (IndexError, ValueError) as exc:
        raise ValueError("invalid .kbm: bad header field") from exc
    if size <= 0:
        raise ValueError("invalid .kbm: map size must be positive")
    if first > last:
        raise ValueError("invalid .kbm: first note is above last note")

    mapping = []
    for line in lines[7 : 7 + size]:
        token = line.split()[0]
        if token.lower() == "x":
            mapping.append(None)
            continue
        degree = int(token)
        if degree < 0:
            raise ValueError("invalid .kbm: negative scale degree")
        mapping.append(degree)
    mapping.extend([None] * (size - len(mapping)))

    return KeyboardMap(
        size,
        first,
        last,
        middle,
        reference_note,
        reference_frequency,
        formal_octave,
        mapping,
    )


def validate_kbm(kbm, scale):
    k = len(scale.degrees)
    octave = kbm.formal_octave or k
    if octave != k:
        raise ValueError(
            f"unsupported .kbm: formal octave is degree {octave}, "
            f"but the scale has {k} degrees per octave"
        )
    for degree in kbm.mapping:
        if degree is not None and degree >= k:
            raise ValueError(
                f"unsupported .kbm: degree {degree} exceeds scale size {k}"
            )


def mapped_keys(kbm, scale):
    """Yield (midi_key, scale_degree, period_index) for retuned keys."""
    k = len(scale.degrees)
    if kbm is None:
        for key in range(128):
            yield key, key % k, key // k
        return

    for key in range(max(0, kbm.first), min(127, kbm.last) + 1):
        degree = kbm.mapping[(key - kbm.middle) % kbm.size]
        if degree is None:
            continue
        yield key, degree, (key - kbm.middle) // kbm.size


def used_degrees(kbm, scale):
    return sorted({degree for _, degree, _ in mapped_keys(kbm, scale)})
