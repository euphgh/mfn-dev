from DesignTree.Utils import HierInstPath, PortDir

class InstancePort:
    """
    wire unit, not bundle
    user should not direct create InstancePort
    should use DesignManager.addInstancePortFromBundle
    """

    def __init__(self) -> None:
        self.instPath = HierInstPath.empty()
        self.moduleName = str()
        self.portWireName = str()
        self.range = tuple[int, int]()
        self.wireDir = PortDir.EMPTY
        self.isLeaf = False
        self.connec = list["InstancePort"]()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, InstancePort):
            return (
                self.instPath == other.instPath
                and self.portWireName == other.portWireName
            )
        return False

    def __hash__(self):
        return hash(self.instPath.__str__() + self.portWireName)

    def leaves(self) -> list["InstancePort"]:
        if self.isLeaf:
            return [self]
        res: list["InstancePort"] = []
        for connec in self.connec:
            res.extend(connec.leaves())
        return res

    def __str__(self) -> str:
        if self.isLeaf:
            return f"leaf: {self.instPath.__str__()}:{self.portWireName}:{self.wireDir}"
        else:
            return f"container: {self.instPath.__str__()}:{self.portWireName}:{self.wireDir}"
