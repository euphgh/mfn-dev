import json
import sys
import os
import glob
from typing import Any
from dataclasses import dataclass
from DesignTree import HierInstPath, LogicalTopoGraph
from io import TextIOWrapper


@dataclass(frozen=True)
class AdHocConnection:
    adhoc: str
    logical_port: str
    msb: int
    lsb: int

    @staticmethod
    def fromJson(json: dict[str, Any]) -> "AdHocConnection":
        portLeft = json["portLeft"]
        portRight = json["portRight"]
        repLeft = json["repLeft"]
        repRight = json["repRight"]
        if portLeft < portRight:
            raise Exception(f"portLeft({portLeft}) < portRight({portRight})")
        if portRight != 0:
            raise Exception(f"portRight({portRight}) is not 0")
        if (portLeft - portRight) != (repLeft - repRight):
            raise Exception(
                f"rep width({repLeft - repRight}) not equal to port width({portLeft - portRight})"
            )
        return AdHocConnection(json["name"], json["logicalPort"], repLeft, repRight)

    @staticmethod
    def empty() -> "AdHocConnection":
        return AdHocConnection("", "", 0, 0)


repeater_info_dir = sys.argv[1]
logical_info = sys.argv[2]
hierTree: LogicalTopoGraph = LogicalTopoGraph(logical_info)
success = hierTree.tops({"mpu"})


def jsonName(json: dict[str, Any]):
    container = json["container"]
    instance = json["instance"]
    totalWidth: int = 0
    if json["data in"].__len__() != 0:
        for data_in in json["data in"]:
            totalWidth = totalWidth + (data_in["portLeft"] - data_in["portRight"] + 1)
    if json["data out"].__len__() != 0:
        for data_out in json["data out"]:
            totalWidth = totalWidth + (data_out["portLeft"] - data_out["portRight"] + 1)
    return f"[{instance}, {container}, {totalWidth * json['pd']}]"
class FgcgRepeater:
    @staticmethod
    def fromJson(json: dict[str, Any]) -> "FgcgRepeater|None":
        fgcg = FgcgRepeater()
        try:
            fgcg.container = json["container"]
            fgcg.instance = json["instance"]
            fgcg.clock = json["clk"]
            fgcg.cell_num = json["pd"]
            fgcg.interconnection = json["interconnection"]
            fgcg.fgcg_in = json["fgcg in"]
            fgcg.fgcg_out = json["fgcg out"]
            fgcg.data_in = {}
            for data_in in json["data in"]:
                adhoc = AdHocConnection.fromJson(data_in)
                fgcg.data_in[adhoc.logical_port] = adhoc
            fgcg.data_out = {}
            for data_out in json["data out"]:
                adhoc = AdHocConnection.fromJson(data_out)
                fgcg.data_out[adhoc.logical_port] = adhoc
            if fgcg.data_in.keys() != fgcg.data_out.keys():
                raise Exception("data in keys not equal to data out keys")
        except KeyError as ke:
            print(f"Fail to parser FGCG: Not found key {ke} in {jsonName(json)}")
            return None
        except Exception as e:
            print(f"Fail to parser FGCG: {e} in {jsonName(json)}")
            return None
        return fgcg

    def __init__(self) -> None:
        self.container: str
        self.instance: str
        self.clock: str
        self.cell_num: int
        self.interconnection: str
        self.fgcg_in: str
        self.fgcg_out: str
        self.data_in: dict[str, AdHocConnection]
        self.data_out: dict[str, AdHocConnection] = {}

def rep_suffix(index: int, n: int) -> str:
    if index == 0:
        return ""
    elif index == n - 1:
        return "rep"
    else:
        return f"rep{index - 1}"


def connixRepInstPath(
    fgcg: FgcgRepeater,
    adhoc: AdHocConnection,
    cell_idx: int,
    bit_idx: int,
    logical_port: str = "rep_dat_out",
):
    rep_const_path = "NML_REG_TYPE.NMML_MULTI_REG.NML_EACH_REG"
    signal_name = (
        f"{fgcg.instance}/{rep_const_path}[{cell_idx}].u_fgcg/{logical_port}_reg"
    )
    if (adhoc.lsb == adhoc.msb) and (adhoc.lsb == 0):
        return signal_name
    else:
        return f"{signal_name}[{bit_idx}]"


def connecRepInstPath(
    fgcg: FgcgRepeater,
    adhoc: AdHocConnection,
    cell_idx: int,
    bit_idx: int,
    logical_port: str,
):
    instPath = f"{fgcg.container}_rep_{fgcg.clock}"
    suffix = ""
    if cell_idx < fgcg.cell_num - 1:
        suffix = f"rep{cell_idx}"
    else:
        suffix = "rep"
    signal_name = f"{instPath}/{fgcg.interconnection}_{logical_port}_{suffix}_reg"
    if (adhoc.lsb == adhoc.msb) and (adhoc.lsb == 0):
        return signal_name
    else:
        return f"{signal_name}[{bit_idx - adhoc.lsb}]"


def matchFgcg(fgcg: FgcgRepeater):
    res = list[tuple[str, str]]()
    for cell_idx in range(fgcg.cell_num):
        # repeater data field
        for logical_port, adhoc in fgcg.data_in.items():
            for bit_idx in range(adhoc.lsb, adhoc.msb + 1):
                connec_path = connecRepInstPath(
                    fgcg, adhoc, cell_idx, bit_idx, logical_port
                )
                connix_path = connixRepInstPath(
                    fgcg, adhoc, cell_idx, bit_idx, "rep_dat_out"
                )
                res.append((connec_path, connix_path))
        # clock enable
        connec_enable = connecRepInstPath(
            fgcg, AdHocConnection.empty(), cell_idx, 0, "fgcg_clk_en"
        )
        connix_enable = connixRepInstPath(
            fgcg, AdHocConnection.empty(), cell_idx, 0, "fgcg_en"
        )
        res.append((connec_enable, connix_enable))
    return res


ref_work = "r:/FMWORK_REF_MPU"
imp_work = "i:/FMWORK_IMPL_MPU"


def printMatch(matches: list[tuple[str, str]], container: str, out_file: TextIOWrapper):
    for prefix in hierTree.outer(HierInstPath(container, ())):
        for match in matches:
            ref_prefix = f"{ref_work}/{prefix.join('/')}"
            impl_prefix = f"{imp_work}/{prefix.join('/')}"
            out_file.write(
                f"set_user_match {ref_prefix}/{match[0]} {impl_prefix}/{match[1]}\n"
            )


if __name__ == "__main__":
    pattern = os.path.join(repeater_info_dir, "*_repeater.json")
    json_files = glob.glob(pattern)
    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as f:
            data: dict[str, list[dict[str, Any]]] = json.load(f)
        fgcg_repeaters = list[FgcgRepeater]()
        json_fgcg_array = data["fgcg repeater"]
        print(f"Found {json_fgcg_array.__len__()} FGCG in {json_file}")
        for x in json_fgcg_array:
            fgcg = FgcgRepeater.fromJson(x)
            if fgcg is not None:
                fgcg_repeaters.append(fgcg)
        print(
            f"Total: {json_fgcg_array.__len__()}, Valid: {fgcg_repeaters.__len__()} in {json_file}"
        )
        with open("output.tcl", "w", encoding="utf-8") as out_file:
            for fgcg in fgcg_repeaters:
                printMatch(matchFgcg(fgcg), fgcg.container, out_file)
