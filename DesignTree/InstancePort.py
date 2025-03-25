from DesignTree.Utils import PortDir, HierInstPath
from typing import Optional
import yaml


class ModuleNode:
    def __init__(self, name: str) -> None:
        self.name = name
        # from instance name to
        self.subs = dict[str, "Optional[ModuleNode]"]()

    def isLeaf(self):
        return self.subs.__len__() == 0


class InstanceModuleMap:

    def __init__(self, yamlFile: str) -> None:
        # container -> dict{ instance -> container }
        self.containerDict = dict[str, dict[str, str]]()
        self.nodeDict = dict[str, ModuleNode]()
        self.roots = set[str]()
        with open(yamlFile, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            assert isinstance(data, dict)

            assert "CONTAINER_CLASS_NAMES" in data
            for pair in data["CONTAINER_CLASS_NAMES"]:
                assert isinstance(pair, str)
                pModule = pair.strip()
                self.containerDict[pModule] = dict[str, str]()
                self.nodeDict[pModule] = ModuleNode(pModule)
                self.roots.add(pModule)

            assert "ALL_BLOCK_INSTANCE_PARENT_PATH" in data
            for pair in data["ALL_BLOCK_INSTANCE_PARENT_PATH"]:
                assert isinstance(pair, str)
                pathName, subModule = pair.split(":")
                pModule, instanceName = pathName.split(".")
                self.containerDict[pModule][instanceName] = subModule
                if subModule in self.nodeDict:
                    self.nodeDict[pModule].subs[instanceName] = self.nodeDict[subModule]
                else:
                    leafNode = ModuleNode(subModule)
                    self.nodeDict[subModule] = leafNode
                    self.nodeDict[pModule].subs[instanceName] = leafNode

                if subModule in self.roots:
                    self.roots.remove(subModule)

    def isLeaf(self, moduleName: str) -> Optional[bool]:
        if moduleName in self.nodeDict:
            return self.nodeDict[moduleName].isLeaf()
        else:
            return None

    def __getitem__(self, instPath: HierInstPath) -> Optional[str]:
        assert instPath.isAbs
        if instPath.names.__len__() == 0:
            return None
        if instPath.names.__len__() == 1:
            return instPath.names[0]
        currentDict = None
        currentContainerName = instPath.names[0]
        for name in instPath.names[1:]:
            currentDict = self.containerDict[currentContainerName]
            currentContainerName = currentDict[name]
        return currentContainerName

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
