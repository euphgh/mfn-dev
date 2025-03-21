from enum import Enum
# hierarchy instance name
# mutable
class HierInstPath:
    # fullName: foo.bar
    def __init__(self, fullName:str) -> None:
        self.nameList = fullName.split(".")

    def __str__(self) -> str:
        return ".".join(self.nameList)

    def append(self, tail: "HierInstPath") -> None:
        self.nameList.extend(tail.nameList)
    
    def __eq__(self, value: object) -> bool:
        if isinstance(value, HierInstPath):
            return self.__str__() == value.__str__()
        return False

    def __hash__(self) -> int:
        return hash(self.__str__())

class PortDir(Enum):

    INPUT = 1
    OUTPUT = 2
    INOUT = 3

    @staticmethod
    def fromStr(dir:str)-> "PortDir":
        if dir == "receive":
            return PortDir.INPUT
        if dir == "transmit":
            return PortDir.OUTPUT
        if dir == "input":
            return PortDir.INPUT
        if dir == "output":
            return PortDir.OUTPUT
        if dir == "inout":
            return PortDir.INOUT
        assert False, f"Direct str {dir} is not expected"