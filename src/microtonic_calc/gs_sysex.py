from mido import Message


ROLAND_ID = (0x41, 0x10)
GS_MODEL = 0x42
DEVICE_ID = 0x12
PARAM_ADDR = 0x40
FIXED_BYTE = 0x40
GS_SCALE_TUNING = 0x46


def gs_checksum(address_bytes: list[int], data_bytes: list[int]) -> int:
    return (128 - sum(address_bytes + data_bytes) % 128) & 127


def build_gs_scale_tuning_sysex(channel: int, offsets: list[int]) -> Message:
    part = 0x11 + channel
    filled = [o if o is not None else 64 for o in offsets]
    addr = [PARAM_ADDR, part, FIXED_BYTE]
    ck = gs_checksum(addr, filled)
    data = list(ROLAND_ID) + [GS_MODEL, DEVICE_ID] + addr + filled + [ck]
    return Message("sysex", data=tuple(data))
