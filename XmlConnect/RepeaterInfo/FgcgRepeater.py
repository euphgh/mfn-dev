from .ConnecType import PartSelectConnec, BitConnec
from .ConnecType import PORT_LEFT, PORT_RIGHT, DATA_IN, DATA_OUT, FGCG_IN, FGCG_OUT
from .AbstractRepeater import AbstractRepeater
from typing import Any
from dataclasses import dataclass, field


@dataclass
class FgcgRepeater(AbstractRepeater):
    fgcg_in: BitConnec = BitConnec()
    fgcg_out: BitConnec = BitConnec()
    data_in: dict[str, PartSelectConnec] = field(default_factory=dict)
    data_out: dict[str, PartSelectConnec] = field(default_factory=dict)

    @staticmethod
    def json2str(json: dict[str, Any]):
        container = json["container"]
        instance = json["instance"]
        totalWidth: int = 0
        if json[DATA_IN].__len__() != 0:
            for data_in in json[DATA_IN]:
                totalWidth = totalWidth + (data_in[PORT_LEFT] - data_in[PORT_RIGHT] + 1)
        if json[DATA_OUT].__len__() != 0:
            for data_out in json[DATA_OUT]:
                totalWidth = totalWidth + (
                    data_out[PORT_LEFT] - data_out[PORT_RIGHT] + 1
                )
        return f"{container}/{instance}[{totalWidth * json['pd']}]"

    @classmethod
    def fromJson(cls, container: str, clock: str, json: dict[str, Any]):
        self = super().fromJson(container, clock, json)
        self.fgcg_in = BitConnec.fromJson(json[FGCG_IN])
        self.fgcg_out = BitConnec.fromJson(json[FGCG_OUT])
        self.data_in = {}
        for data_in in json[DATA_IN]:
            part_select = PartSelectConnec.fromJson(data_in)
            self.data_in[part_select.logical_port] = part_select
        self.data_out = {}
        for data_out in json[DATA_OUT]:
            part_select = PartSelectConnec.fromJson(data_out)
            self.data_out[part_select.logical_port] = part_select
        if self.data_in.keys() != self.data_out.keys():
            raise Exception("data in keys not equal to data out keys")
        return self

    def dataPaths(self, cell_idx: int, part_select: PartSelectConnec):
        pairs = list[tuple[str, str]]()
        # connectivity1.0 inst path
        instPath = f"{self.container}_rep_{self.clock}"
        logical_port = part_select.logical_port
        suffix = ""
        if cell_idx < self.cell_num - 1:
            suffix = f"rep{cell_idx}"
        else:
            suffix = "rep"
        connec = f"{instPath}/{self.interconnection}_{logical_port}_{suffix}_reg"
        # connix
        rep_const_path = "NML_REG_TYPE.NMML_MULTI_REG.NML_EACH_REG"
        connix = f"{self.instance}/{rep_const_path}[{cell_idx}].u_fgcg/rep_dat_out_reg"
        for bit_idx in range(part_select.lsb_connec, part_select.msb_connec + 1):
            pairs.append(
                (
                    f"{connec}[{bit_idx - part_select.lsb_connec}]",
                    f"{connix}[{bit_idx}]",
                )
            )
        return pairs

    def clockGatePath(self, cell_idx: int, fgcg_in: BitConnec, fgcg_out: BitConnec):
        # connectivity1.0 inst path
        instPath = f"{self.container}_rep_{self.clock}"
        logical_port = fgcg_in.logical_port
        suffix = ""
        if cell_idx < self.cell_num - 1:
            suffix = f"rep{cell_idx}"
        else:
            suffix = "rep"
        connec = f"{instPath}/{self.interconnection}_{logical_port}_{suffix}_reg"
        # connix
        rep_const_path = "NML_REG_TYPE.NMML_MULTI_REG.NML_EACH_REG"
        connix = f"{self.instance}/{rep_const_path}[{cell_idx}].u_fgcg/fgcg_en_reg"
        return (connec, connix)

    def match(self) -> list[tuple[str, str]]:
        res = list[tuple[str, str]]()
        for cell_idx in range(self.cell_num):
            # repeater data field
            for _, part_select in self.data_in.items():
                res.extend(self.dataPaths(cell_idx, part_select))
            res.append(self.clockGatePath(cell_idx, self.fgcg_in, self.fgcg_out))
        return res