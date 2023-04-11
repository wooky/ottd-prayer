from __future__ import annotations

import logging
import lzma
import struct
import sys
from dataclasses import dataclass
from typing import Any

from openttd_protocol.wire.exceptions import PacketTooShort
from openttd_protocol.wire.read import (
    read_bytes,
    read_uint8,
    read_uint16,
    read_uint32,
    read_uint64,
)

logger = logging.getLogger(__name__)
LOGLEVEL_TRACE = 5
SPECIAL_CHUNKS: list[bytes] = [b"AIPL", b"GSDT"]
MIN_SAVELOAD_VERSION = 296


def _trace(msg: str, *args: object) -> None:
    logger.log(LOGLEVEL_TRACE, msg, *args)


@dataclass
class ChRiff:
    chunk: bytes

    @staticmethod
    def create(type: int, data: memoryview) -> tuple[ChRiff, memoryview]:
        length, data = read_uint24(data)
        length |= (type >> 4) << 24
        _trace("RIFF size should be %d", length)
        chunk, data = read_bytes(data, length)
        return ChRiff(chunk=chunk), data


class ChTableReader:
    StructKey = tuple[str, ...]
    Header = list[tuple[int, str]]
    Row = dict[str, Any]
    root_struct_key: StructKey = ()

    def __init__(self) -> None:
        self.structs: dict[ChTableReader.StructKey, ChTableReader.Header] = {}
        self.structs_to_process: list[ChTableReader.StructKey] = [
            ChTableReader.root_struct_key
        ]
        self.special = False

    def read_header(self, data: memoryview) -> memoryview:
        header_size, data = gamma(data)
        _trace("Table header size should be %d", header_size - 1)
        expected_remaining_size = len(data) - header_size + 1

        while len(self.structs_to_process) != 0:
            key = self.structs_to_process.pop(0)
            _trace("Reading header struct %s", key)
            header_struct, data = self._read_header_struct(key, data)
            self.structs[key] = header_struct

        if len(data) < expected_remaining_size:
            raise Exception(
                "Table header size mismatch: expected ",
                expected_remaining_size,
                " bytes to remain, got ",
                len(data),
            )

        return data

    def _read_header_struct(
        self, struct_name: StructKey, data: memoryview
    ) -> tuple[Header, memoryview]:
        structs_to_process_idx = 0
        header: ChTableReader.Header = []
        while True:
            field_type, data = read_uint8(data)
            if field_type == 0:
                return header, data

            key_length, data = gamma(data)
            key_raw, data = read_bytes(data, key_length)
            key = key_raw.decode("UTF-8")
            _trace("Read field type %d named %s", field_type, key)
            header.append((field_type, key))

            if field_type & 0xF == 11:
                self.structs_to_process.insert(
                    structs_to_process_idx, struct_name + (key,)
                )
                structs_to_process_idx += 1

    def read_row(self, row_size: int, data: memoryview) -> tuple[Row, memoryview]:
        _trace("Table row size should be %d", row_size - 1)
        if row_size == 1:
            # This is an array with unallocated data
            return {}, data
        expected_remaining_size = len(data) - row_size + 1
        row, data = self._read_row_struct(ChTableReader.root_struct_key, data)
        if len(data) != expected_remaining_size and self.special:
            has_script_data, data = read_uint8(data)
            if has_script_data != 0:
                _trace("Reading script data")
                _, data = self._read_script_data(data)
        if len(data) != expected_remaining_size:
            raise Exception(
                "Table row size mismatch: expected ",
                expected_remaining_size,
                " bytes to remain, got ",
                len(data),
            )
        return row, data

    def _read_row_struct(
        self, struct_name: StructKey, data: memoryview
    ) -> tuple[Row, memoryview]:
        row: ChTableReader.Row = {}
        for field_type, key in self.structs[struct_name]:
            repeat = 1
            value = None
            if field_type & 0x10:
                repeat, data = gamma(data)
            _trace("Reading field '%s' %d time(s)", key, repeat)
            match field_type & 0xF:
                case 1 | 2:
                    for _ in range(repeat):
                        _, data = read_uint8(data)
                case 3 | 4 | 9:
                    for _ in range(repeat):
                        _, data = read_uint16(data)
                case 5 | 6:
                    for _ in range(repeat):
                        _, data = read_uint32(data)
                case 7 | 8:
                    for _ in range(repeat):
                        _, data = read_uint64(data)
                case 10:
                    value, data = read_bytes(data, repeat)
                case 11:
                    for _ in range(repeat):
                        _, data = self._read_row_struct(struct_name + (key,), data)
                case _ as x:
                    raise Exception("Unhandled field type ", x)
            row[key] = value
        return row, data

    def _read_script_data(self, data: memoryview) -> tuple[None, memoryview]:
        field_type, data = read_uint8(data)
        _trace("Reading SQSL field type %d", field_type)
        match field_type:
            case 0:
                _, data = read_uint64(data)
            case 1:
                size, data = read_uint8(data)
                _, data = read_bytes(data, size)
            case 2:
                marker, post_marker_data = read_uint8(data)
                while marker != 0xFF:
                    _trace("Reading SQSL array element")
                    _, data = self._read_script_data(data)
                    marker, post_marker_data = read_uint8(data)
                _trace("No more SQSL array elements")
                data = post_marker_data
            case 3:
                marker, post_marker_data = read_uint8(data)
                while marker != 0xFF:
                    _trace("Reading SQSL table key")
                    _, data = self._read_script_data(data)
                    _trace("Reading SQSL table value")
                    _, data = self._read_script_data(data)
                    marker, post_marker_data = read_uint8(data)
                _trace("No more SQSL table elements")
                data = post_marker_data
            case 4:
                _, data = read_uint8(data)
            case 5:
                pass
            case _ as x:
                raise Exception("Unhandled SQSL field type", x)

        return (None, data)


@dataclass
class ChTable:
    elements: list[dict[str, Any]]

    @staticmethod
    def create(data: memoryview, special: bool) -> tuple[ChTable, memoryview]:
        elements: list[dict[str, Any]] = []
        reader = ChTableReader()
        data = reader.read_header(data)
        reader.special = special
        while True:
            row_size, data = gamma(data)
            if row_size == 0:
                break
            row, data = reader.read_row(row_size, data)
            elements.append(row)
        return ChTable(elements=elements), data


@dataclass
class ChSparseTable:
    elements: dict[int, dict[str, Any]]

    @staticmethod
    def create(data: memoryview) -> tuple[ChSparseTable, memoryview]:
        elements: dict[int, dict[str, Any]] = {}
        reader = ChTableReader()
        data = reader.read_header(data)
        while True:
            total_row_size, data = gamma(data)
            if total_row_size == 0:
                break
            last_data_len = len(data)
            idx, data = gamma(data)
            _trace("Set table index to %d", idx)
            row_size = total_row_size - last_data_len + len(data)
            row, data = reader.read_row(row_size, data)
            elements[idx] = row
        return ChSparseTable(elements=elements), data


class SaveloadBuffer:
    """TODO use incremental decompression"""

    def __init__(self) -> None:
        self.buf: list[int] = []

    def append(self, b: memoryview) -> None:
        self.buf.extend(b)

    def to_bytes(self) -> bytes:
        return bytes(self.buf)

    def decode(self) -> dict[str, Any]:
        raw_data = memoryview(self.to_bytes())
        compression, raw_data = read_bytes(raw_data, 4)
        version, raw_data = read_uint16(raw_data)
        _, raw_data = read_uint16(raw_data)
        if version < MIN_SAVELOAD_VERSION:
            raise Exception("Unsupported version ", version)

        match compression:
            case b"OTTN":
                data = raw_data
            case b"OTTX":
                decompressed_data = lzma.decompress(raw_data)
                data = memoryview(decompressed_data)
            case _:
                raise Exception("Unsupported compression mode ", compression)

        chunks: dict[str, Any] = {}
        while True:
            chunk_name, data = read_bytes(data, 4)
            if chunk_name == b"\x00\x00\x00\x00":
                if len(data) != 0:
                    raise Exception(
                        "Unexpected end of data, still got ", len(data), " bytes to go"
                    )
                return chunks

            _trace("Got header %s", chunk_name)
            chunk_type, data = read_uint8(data)
            chunk: Any
            match chunk_type & 0xF:
                case 0:
                    chunk, data = ChRiff.create(chunk_type, data)
                case 3:
                    chunk, data = ChTable.create(data, chunk_name in SPECIAL_CHUNKS)
                case 4:
                    chunk, data = ChSparseTable.create(data)
            chunks[chunk_name.decode("UTF-8")] = chunk


def gamma(data: memoryview) -> tuple[int, memoryview]:
    res, data = read_uint8(data)
    mask = 0x80
    while res & mask != 0:
        next_byte, data = read_uint8(data)
        res = ((res & ~mask) << 8) | next_byte
        mask <<= 7
    return res, data


def read_uint24(data: memoryview) -> tuple[int, memoryview]:
    try:
        buf = b"\x00" + bytes(data[:3])
        value = struct.unpack_from(">I", buf, 0)
    except struct.error:
        raise PacketTooShort from None
    return value[0], data[3:]


if __name__ == "__main__":
    logging.basicConfig(level=LOGLEVEL_TRACE)
    saveload = SaveloadBuffer()
    with open(sys.argv[1], "rb") as f:
        saveload.append(memoryview(f.read()))
    saveload.decode()
