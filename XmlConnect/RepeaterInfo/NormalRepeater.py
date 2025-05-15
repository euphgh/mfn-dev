from .ConnecType import WireConnec
from .ConnecType import DATA_IN, DATA_OUT
from .AbstractRepeater import AbstractRepeater
from typing import Any
from dataclasses import dataclass
import re

single_signal_patterns = [r"signal_\d+_\d+"]


def is_single_logical_port(s: str) -> bool:
    for p in single_signal_patterns:
        if re.fullmatch(p, s) is not None:
            return True
    return False

@dataclass
class NormalRepeater(AbstractRepeater):
    data_in: WireConnec = WireConnec()
    data_out: WireConnec = WireConnec()

    @staticmethod
    def json2str(json: dict[str, Any]):
        container = json["container"]
        instance = json["instance"]
        return f"{container}/{instance}"

    @classmethod
    def fromJson(cls, container: str, clock: str, json: dict[str, Any]):
        self = super().fromJson(container, clock, json)
        self.data_in = WireConnec.fromJson(json[DATA_IN])
        self.data_out = WireConnec.fromJson(json[DATA_OUT])
        if self.data_in.msb != self.data_out.msb:
            raise Exception(
                f"data in msb({self.data_in.msb}) != data out msb({self.data_out.msb})"
            )
        if self.data_in.lsb != self.data_out.lsb:
            raise Exception(
                f"data in lsb({self.data_in.lsb}) != data out lsb({self.data_out.lsb})"
            )
        return self

    def dataPath(self, cell_idx: int, wire_connec: WireConnec):
        pairs = list[tuple[str, str]]()
        pairs = list[tuple[str, str]]()
        # connectivity1.0 inst path
        instPath = f"{self.container}_rep_{self.clock}"
        logical_port = wire_connec.logical_port
        suffix = ""
        if cell_idx < self.cell_num - 1:
            suffix = f"rep{cell_idx}"
        else:
            suffix = "rep"

        connec = f"{instPath}/{self.interconnection}_{logical_port}_{suffix}_reg"
        if is_single_logical_port(logical_port):
            connec = f"{instPath}/{self.interconnection}_{suffix}_reg"

        # connix
        rep_const_path = "NML_REG_TYPE.NMML_MULTI_REG.NML_EACH_REG"
        connix = f"{self.instance}/{rep_const_path}[{cell_idx}].u_reg/rep_dat_out_reg"
        for bit_idx in range(wire_connec.lsb, wire_connec.msb + 1):
            pairs.append((f"{connec}[{bit_idx}]", f"{connix}[{bit_idx}]"))
        return pairs

    def match(self) -> list[tuple[str, str]]:
        res = list[tuple[str, str]]()
        for cell_idx in range(self.cell_num):
            res.extend(self.dataPath(cell_idx, self.data_in))
        return res
