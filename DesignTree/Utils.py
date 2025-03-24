from enum import Enum
import copy


# hierarchy instance name
# mutable
class HierInstPath:
    # fullName: foo.bar
    # if foo is top module name, the parentModuleName is "/", that is abs path
    # else foo is normal module name, the parentModuleName is "foo", is a relative path
    # abs: absolute path or relative path
    def __init__(self, fullName: str, isAbs: bool) -> None:
        self.nameList = fullName.split(".")
        self.isAbs = isAbs

    def toAbs(self, parentInstPath: "HierInstPath"):
        assert parentInstPath.isAbs
        absPath = copy.deepcopy(parentInstPath)
        absPath.append(self)
        return absPath

    def __str__(self) -> str:
        if self.isAbs:
            return "/" + ".".join(self.nameList)
        else:
            return "." + ".".join(self.nameList)

    def append(self, tail: "str|HierInstPath") -> None:
        if isinstance(tail, str):
            self.nameList.append(tail)
        else:
            self.nameList.extend(tail.nameList)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, HierInstPath):
            return self.__str__() == value.__str__()
        return False

    def __hash__(self) -> int:
        return hash(self.__str__())

    @staticmethod
    def empty() -> "HierInstPath":
        return HierInstPath("", False)


class PortDir(Enum):

    EMPTY = 0
    INPUT = 1
    OUTPUT = 2
    INOUT = 3

    @staticmethod
    def fromStr(dir: str) -> "PortDir":
        if dir == "receive":
            return PortDir.INPUT
        if dir == "transmit":
            return PortDir.OUTPUT
        if dir == "output":
            return PortDir.OUTPUT
        if dir == "input":
            return PortDir.INPUT
        if dir == "inout":
            return PortDir.INOUT
        if dir == "bidirect":
            return PortDir.INOUT
        assert False, f"Direct str {dir} is not expected"
