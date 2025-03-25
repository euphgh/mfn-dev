from DesignTree.Utils import PortDir, HierInstPath
from typing import Optional
import yaml


class ModuleNode:
    def __init__(self, name: str) -> None:
        self.name = name
        # from instance name to
        self.next = dict[str, "Optional[ModuleNode]"]()
        self.prev = dict[str, "Optional[ModuleNode]"]()

    def isLeaf(self):
        return self.next.__len__() == 0


class InstanceModuleMap:

    def __init__(self, yamlFile: str) -> None:
        self.nodes = dict[str, ModuleNode]()
        self.roots = set[str]()
        with open(yamlFile, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            assert isinstance(data, dict)

            for line in data["CONTAINER_CLASS_NAMES"]:
                assert isinstance(line, str)
                pModule = line.strip()
                # self.containerDict[pModule] = dict[str, str]()
                self.nodes[pModule] = ModuleNode(pModule)
                self.roots.add(pModule)

            for pair in data["ALL_BLOCK_INSTANCE_PARENT_PATH"]:
                assert isinstance(pair, str)
                pathName, sModule = pair.split(":")
                pModule, instanceName = pathName.split(".")
                # self.containerDict[pModule][instanceName] = sModule

                pModuleNode = self.nodes[pModule]
                # get value if key exist, else insert new value and return
                sModuleNode = self.nodes.setdefault(sModule, ModuleNode(sModule))

                # set double direct link
                pModuleNode.next[instanceName] = sModuleNode
                sModuleNode.prev[instanceName] = pModuleNode

                if sModule in self.roots:
                    self.roots.remove(sModule)

    def isLeaf(self, moduleName: str) -> Optional[bool]:
        if moduleName in self.nodes:
            return self.nodes[moduleName].isLeaf()
        else:
            return None

    def __getitem__(self, instPath: HierInstPath) -> Optional[str]:
        assert instPath.isAbs
        if instPath.names.__len__() == 0:
            return None
        if instPath.names.__len__() == 1:
            return instPath.names[0]

        index = 0
        node: Optional[ModuleNode] = self.nodes[instPath.names[index]]
        while node != None and index < instPath.names.__len__() - 1:
            index += 1
            node = node.next[instPath.names[index]]

        if node is None:
            return None
        else:
            return node.name

# wire unit, not bundle
class InstancePort:

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
