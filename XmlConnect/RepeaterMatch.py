import json
import sys
from typing import Any
from dataclasses import dataclass
from DesignTree import HierInstPath, LogicalTopoGraph


@dataclass(frozen=True)
class AdHocConnection:
    adhoc: str
    logical_port: str
    msb: int
    lsb: int

    @staticmethod
    def fromJson(json: dict[str, Any]) -> "AdHocConnection":
        assert (json["port left"] > 0) and (json["port right"] == 0)
        assert (json["port left"] - json["port right"]) == (
            json["rep left"] - json["rep right"]
        )
        return AdHocConnection(
            json["adhoc"], json["logical port"], json["rep left"], json["rep right"]
        )

    @staticmethod
    def empty() -> "AdHocConnection":
        return AdHocConnection("", "", 0, 0)


repeater_info_json = sys.argv[1]
logical_info = sys.argv[2]
hierTree: LogicalTopoGraph = LogicalTopoGraph(logical_info)
success = hierTree.tops({"mpu"})


class FgcgRepeater:
    def __init__(self, json: dict[str, Any]) -> None:
        self.container: str = json["container"]
        self.instance: str = json["instance"]
        self.clock: str = json["clk"]
        self.cell_num: int = json["pd"]
        self.interconnection: str = json["interconnection"]
        self.fgcg_in: str = json["fgcg in"]
        self.fgcg_out: str = json["fgcg out"]
        self.data_in: dict[str, AdHocConnection] = {}
        for data_in in json["data in"]:
            adhoc = AdHocConnection.fromJson(data_in)
            self.data_in[adhoc.logical_port] = adhoc
        self.data_out: dict[str, AdHocConnection] = {}
        for data_out in json["data out"]:
            adhoc = AdHocConnection.fromJson(data_out)
            self.data_out[adhoc.logical_port] = adhoc
        assert self.data_in.keys() == self.data_out.keys()


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
            for bit_idx in range(adhoc.lsb, adhoc.msb):
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


def printMatch(matches: list[tuple[str, str]], container: str):
    for prefix in hierTree.outer(HierInstPath(container, ())):
        for match in matches:
            ref_prefix = f"{ref_work}/{prefix.join('/')}"
            impl_prefix = f"{imp_work}/{prefix.join('/')}"
            # print(f"set_user_match {ref_prefix}/{match[0]} {impl_prefix}/{match[1]}")
            print(f"{impl_prefix}/{match[1]}")


if __name__ == "__main__":
    with open(repeater_info_json, "r", encoding="utf-8") as f:
        data: dict[str, list[dict[str, Any]]] = json.load(f)
    normal_repeaters = data["normal repeater"]
    fgcg_repeaters = [FgcgRepeater(x) for x in data["fgcg repeater"]]
    for fgcg in fgcg_repeaters:
        printMatch(matchFgcg(fgcg), fgcg.container)
