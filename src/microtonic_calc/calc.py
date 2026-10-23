from itertools import combinations
from math import ceil, floor

PARTS_PER_PORT = 16
DEFAULT_SEARCH_BUDGET = 200_000


def _round_half_up(x):
    return floor(x + 0.5)


def compute_edo(
    n,
    range_neg=-64,
    range_pos=63,
    step=1.0,
    exhaustive=False,
    budget=DEFAULT_SEARCH_BUDGET,
):
    degrees = [1200.0 * i / n for i in range(n)]
    return compute_scale(
        degrees,
        range_neg=range_neg,
        range_pos=range_pos,
        step=step,
        exhaustive=exhaustive,
        budget=budget,
    )


def compute_scale(
    degrees,
    period=1200.0,
    used=None,
    range_neg=-64,
    range_pos=63,
    step=1.0,
    exhaustive=False,
    budget=DEFAULT_SEARCH_BUDGET,
):
    bias = _round_half_up(-range_neg / step)
    used = list(range(len(degrees))) if used is None else sorted(set(used))

    candidates = {}
    for degree in used:
        options = _candidates(degrees[degree], range_neg, range_pos, step, bias)
        if not options:
            raise ValueError(
                f"degree {degree} ({degrees[degree]:.6f} cents) cannot be "
                f"tuned within [{range_neg}, {range_pos}]"
            )
        candidates[degree] = options

    choices = {degree: candidates[degree][0] for degree in used}
    greedy = _channel_count(choices)
    lower = _lower_bound(candidates, greedy)
    optimal = greedy <= lower

    if not optimal:
        choices, proven = _search(
            candidates,
            choices,
            lower,
            greedy,
            1 << 60 if exhaustive else budget,
        )
        optimal = proven

    result = _build(used, choices, degrees, period, step, bias)
    result["optimal"] = optimal
    return result


def _candidates(cents, range_neg, range_pos, step, bias):
    t_floor = floor(cents / 100)
    t_round = _round_half_up(cents / 100)
    preferred = [t_floor]
    if t_round != t_floor:
        preferred.append(t_round)

    t_lo = ceil((cents - range_pos) / 100) - 2
    t_hi = floor((cents - range_neg) / 100) + 2
    rest = []
    for semi in range(t_lo, t_hi + 1):
        if semi in preferred:
            continue
        value = _round_half_up((cents - semi * 100) / step) + bias
        offset = (value - bias) * step
        if range_neg <= offset <= range_pos:
            rest.append((abs(offset), semi, value))
    rest.sort()

    options = []
    for semi in preferred:
        value = _round_half_up((cents - semi * 100) / step) + bias
        offset = (value - bias) * step
        if range_neg <= offset <= range_pos:
            options.append((semi, semi % 12, value))
    for _, semi, value in rest:
        options.append((semi, semi % 12, value))
    return options


def _lower_bound(candidates, greedy):
    forced = {}
    for options in candidates.values():
        if len(options) == 1:
            _, slot, value = options[0]
            forced.setdefault(slot, set()).add(value)
    bound = max((len(values) for values in forced.values()), default=0)
    if bound >= greedy:
        return bound

    slots = sorted({s for opts in candidates.values() for _, s, _ in opts})
    for size in (1, 2, 3):
        for subset in combinations(slots, size):
            allowed = set(subset)
            count = 0
            seen = {slot: set() for slot in subset}
            shared = False
            for options in candidates.values():
                if any(slot not in allowed for _, slot, _ in options):
                    continue
                count += 1
                for _, slot, value in options:
                    if value in seen[slot]:
                        shared = True
                        break
                    seen[slot].add(value)
                if shared:
                    break
            if count and not shared:
                bound = max(bound, (count + size - 1) // size)
                if bound >= greedy:
                    return bound
    return bound


def _channel_count(choices):
    slot_values = {}
    for _, slot, value in choices.values():
        slot_values.setdefault(slot, set()).add(value)
    return max((len(values) for values in slot_values.values()), default=0)


def _search(candidates, choices, lower, best, budget):
    choices = dict(choices)
    best_choices = dict(choices)
    free = sorted(
        (d for d in choices if len(candidates[d]) > 1),
        key=lambda d: len(candidates[d]),
    )

    slot_values = {}
    for degree in choices:
        if degree in free:
            continue
        _, slot, value = choices[degree]
        slot_values.setdefault(slot, {}).setdefault(value, 0)
        slot_values[slot][value] += 1

    nodes = 0
    exhausted = False

    def dfs(index):
        nonlocal best, best_choices, nodes, exhausted
        if exhausted or best <= lower:
            return
        if index == len(free):
            current = max(
                (len(values) for values in slot_values.values()), default=0
            )
            if current < best:
                best = current
                best_choices = dict(choices)
            return

        degree = free[index]
        options = sorted(
            candidates[degree],
            key=lambda option: _option_key(option, slot_values),
        )
        for semi, slot, value in options:
            values = slot_values.setdefault(slot, {})
            values[value] = values.get(value, 0) + 1
            choices[degree] = (semi, slot, value)

            nodes += 1
            if nodes > budget:
                exhausted = True
            elif (
                max(
                    (len(v) for v in slot_values.values()),
                    default=0,
                )
                < best
            ):
                dfs(index + 1)

            values[value] -= 1
            if values[value] == 0:
                del values[value]
            if not values:
                del slot_values[slot]

            if exhausted or best <= lower:
                break

    dfs(0)
    return best_choices, not exhausted


def _option_key(option, slot_values):
    _, slot, value = option
    values = slot_values.get(slot, {})
    new = value not in values
    return (new, len(values) + int(new), slot)


def _build(used, choices, degrees, period, step, bias):
    slot_values = {}
    for degree in used:
        _, slot, value = choices[degree]
        slot_values.setdefault(slot, set()).add(value)

    channel_of = {}
    for slot, values in slot_values.items():
        for rank, value in enumerate(sorted(values)):
            channel_of[(slot, value)] = rank

    channels = max((len(values) for values in slot_values.values()), default=0)
    data = [[None] * 12 for _ in range(channels)]
    mapping = []
    for degree in used:
        semi, slot, value = choices[degree]
        channel = channel_of[(slot, value)]
        data[channel][slot] = value
        mapping.append({"degree": degree, "channel": channel, "semitone": semi})

    return {
        "degrees": list(degrees),
        "period": period,
        "step": step,
        "bias": bias,
        "channels": channels,
        "ports": (channels + PARTS_PER_PORT - 1) // PARTS_PER_PORT,
        "data": data,
        "map": mapping,
    }
