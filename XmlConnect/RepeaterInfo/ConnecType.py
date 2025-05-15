from dataclasses import dataclass
from typing import Any

LOGICAL_PORT = "logicalPort"
PORT_LEFT = "portLeft"
PORT_RIGHT = "portRight"
REP_LEFT = "repLeft"
REP_RIGHT = "repRight"
DATA_IN = "data in"
DATA_OUT = "data out"
FGCG_IN = "fgcg in"
FGCG_OUT = "fgcg out"


@dataclass(frozen=True)
class BitConnec:
    name: str = ""
    logical_port: str = ""

    @classmethod
    def fromJson(cls, json: dict[str, Any]):
        return cls(
            json["name"],
            json[LOGICAL_PORT],
        )


@dataclass(frozen=True)
class WireConnec(BitConnec):
    msb: int = 0
    lsb: int = 0

    @classmethod
    def fromJson(cls, json: dict[str, Any]):
        return cls(
            json["name"],
            json[LOGICAL_PORT],
            json[PORT_LEFT],
            json[PORT_RIGHT],
        )


@dataclass(frozen=True)
class PartSelectConnec(WireConnec):
    msb_connec: int = 0
    lsb_connec: int = 0

    @classmethod
    def fromJson(cls, json: dict[str, Any]):
        portLeft = json[PORT_LEFT]
        portRight = json[PORT_RIGHT]
        repLeft = json[REP_LEFT]
        repRight = json[REP_RIGHT]
        if portLeft < portRight:
            raise Exception(f"portLeft({portLeft}) < portRight({portRight})")
        if portRight != 0:
            raise Exception(f"portRight({portRight}) is not 0")
        if (portLeft - portRight) != (repLeft - repRight):
            raise Exception(
                f"rep width({repLeft - repRight}) not equal to port width({portLeft - portRight})"
            )
        return cls(
            json["name"],
            json[LOGICAL_PORT],
            portLeft,
            portRight,
            repLeft,
            repRight,
        )

    @classmethod
    def empty(cls):
        return cls("", "", 0, 0, 0, 0)


