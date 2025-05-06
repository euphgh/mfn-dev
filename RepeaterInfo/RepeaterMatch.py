import json
import sys
from typing import Any
from dataclasses import dataclass


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
    logical_port: str,
    adhoc: AdHocConnection,
    cell_idx: int,
    bit_idx: int,
):
    rep_const_path = "NML_REG_TYPE.NMML_MULTI_REG.NML_EACH_REG"
    return f"{fgcg.container}/{fgcg.instance}/{rep_const_path}{cell_idx}.u_fgcg/rep_data_out[{bit_idx}]"


def connecRepInstPath(
    fgcg: FgcgRepeater,
    logical_port: str,
    adhoc: AdHocConnection,
    cell_idx: int,
    bit_idx: int,
):
    instPath = f"{fgcg.container}/{fgcg.container}_rep_{fgcg.clock}"
    suffix = ""
    if cell_idx == 0:
        suffix = ""
    elif (cell_idx < fgcg.cell_num) and (cell_idx):
        suffix = f"rep{cell_idx - 1}"
    else:
        suffix = "rep"
    return f"{instPath}/{fgcg.interconnection}_{logical_port}{suffix}[{bit_idx - adhoc.lsb}]"


def matchFgcg(fgcg: FgcgRepeater):
    matchTcl = list[str]()
    for cell_idx in range(fgcg.cell_num):
        # repeater data field
        for logical_port, adhoc in fgcg.data_in.items():
            for bit_idx in range(adhoc.lsb, adhoc.msb):
                connec_path = connecRepInstPath(
                    fgcg, logical_port, adhoc, cell_idx, bit_idx
                )
                connix_path = connixRepInstPath(
                    fgcg, logical_port, adhoc, cell_idx, bit_idx
                )
                matchTcl.append(f"set_user_match {connec_path} {connix_path}")
        # clock enable
        # connecEnable = connecRepInstPath(
        #     fgcg, "fgcg_clk_en", AdHocConnection.empty(), cell_idx, 0
        # )
        # connixEnable = connixRepInstPath(fgcg, logical_port, adhoc, cell_idx, 0)
        # matchTcl.append(f"set_user_match {connecEnable} {connixEnable}")
    return "\n".join(matchTcl)


if __name__ == "__main__":
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data: dict[str, list[dict[str, Any]]] = json.load(f)
    normal_repeaters = data["normal repeater"]
    fgcg_repeaters = [FgcgRepeater(x) for x in data["fgcg repeater"]]
    for fgcg in fgcg_repeaters:
        print(matchFgcg(fgcg))
