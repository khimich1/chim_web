"""Best-effort audio duration extraction for upload validation."""

from __future__ import annotations

import struct


def parse_audio_duration_sec(data: bytes, mime_type: str) -> float | None:
    """Return duration in seconds when metadata can be read, else None."""
    if mime_type == "audio/webm":
        return _parse_webm_duration(data)
    if mime_type == "audio/ogg":
        return _parse_ogg_duration(data)
    return None


def _parse_webm_duration(data: bytes) -> float | None:
    """Parse Duration element (0x4489) from WebM/Matroska EBML."""
    idx = 0
    length = len(data)
    while idx + 4 < length:
        element_id, id_size = _read_vint(data, idx)
        if element_id is None:
            break
        idx += id_size
        size, size_len = _read_vint(data, idx)
        if size is None:
            break
        idx += size_len
        if element_id == 0x4489 and size == 8 and idx + 8 <= length:
            return struct.unpack(">d", data[idx : idx + 8])[0]
        if element_id in (0x18538067, 0x1549A966):  # Segment, Info — search inside
            end = min(idx + size, length)
            nested = _parse_webm_duration(data[idx:end])
            if nested is not None:
                return nested
        idx += size
    return None


def _parse_ogg_duration(data: bytes) -> float | None:
    """Estimate duration from last OGG page granule position and sample rate."""
    idx = 0
    length = len(data)
    sample_rate: int | None = None
    last_granule = 0

    while idx + 27 <= length:
        if data[idx : idx + 4] != b"OggS":
            break
        header_type = data[idx + 5]
        granule = struct.unpack("<Q", data[idx + 6 : idx + 14])[0]
        page_segments = data[idx + 26]
        segment_table_end = idx + 27 + page_segments
        if segment_table_end > length:
            break
        page_size = sum(data[idx + 27 : segment_table_end])
        page_end = segment_table_end + page_size
        if page_end > length:
            break

        if header_type & 0x02:  # bos — read sample rate from OpusHead
            payload_start = segment_table_end
            if data[payload_start : payload_start + 8] == b"OpusHead":
                # OpusHead: skip 12 bytes header to pre-skip, then not sample rate
                pass
            elif data[payload_start : payload_start + 7] == b"vorbis":
                # Vorbis identification: sample rate at byte 12 (LE u32)
                if payload_start + 16 <= page_end:
                    sample_rate = struct.unpack(
                        "<I",
                        data[payload_start + 12 : payload_start + 16],
                    )[0]

        if granule != 0xFFFFFFFFFFFFFFFF:
            last_granule = granule
        idx = page_end

    if sample_rate and sample_rate > 0 and last_granule > 0:
        return last_granule / sample_rate
    return None


def _read_vint(data: bytes, offset: int) -> tuple[int | None, int]:
    if offset >= len(data):
        return None, 0
    first = data[offset]
    if first == 0:
        return None, 0
    mask = 0x80
    length = 1
    while length <= 8 and not (first & mask):
        mask >>= 1
        length += 1
    if length > 8 or offset + length > len(data):
        return None, 0
    value = first & (mask - 1)
    for i in range(1, length):
        value = (value << 8) | data[offset + i]
    return value, length
