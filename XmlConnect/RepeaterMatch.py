import json
import sys
from typing import Any
from DesignTree import HierInstPath, LogicalTopoGraph
from io import TextIOWrapper
from RepeaterInfo import FgcgRepeater, NormalRepeater, repJsonParser

repeater_info = sys.argv[1]
logical_info = sys.argv[2]
hierTree: LogicalTopoGraph = LogicalTopoGraph(logical_info)
success = hierTree.tops({"mpu"})


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
    data = dict[str, Any]()
    with open(repeater_info, "r", encoding="utf-8") as f:
        data = json.load(f)
    fgcg_repeaters = repJsonParser(FgcgRepeater, data["fgcg"])
    norm_repeaters = repJsonParser(NormalRepeater, data["normal"])
    with open("output.tcl", "w", encoding="utf-8") as out_file:
        for fgcg in fgcg_repeaters:
            printMatch(fgcg.match(), fgcg.container, out_file)
        for norm in norm_repeaters:
            printMatch(norm.match(), norm.container, out_file)