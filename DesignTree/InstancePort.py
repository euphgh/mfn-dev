from DesignTree.Utils import PortDir, HierInstPath
from typing import Optional
import yaml


# node of hierarchical tree
class ModuleNode:
    def __init__(self, name: str) -> None:
        self.name: str = name
        # from instance name to
        self.next = dict[str, ModuleNode]()
        self.prev = dict[str, ModuleNode]()

    def isLeaf(self):
        return self.next.__len__() == 0


# hierarchical tree
class HierTree:

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

    def isLeaf(self, moduleName: str) -> bool:
        node = self.nodes.get(moduleName)
        if node is not None:
            return node.isLeaf()
        else:
            return False

    def containers(self) -> set[str]:
        containerNodes = filter(lambda x: not x.isLeaf(), self.nodes.values())
        return set(map(lambda x: x.name, containerNodes))

    def leaves(self) -> set[str]:
        leafNodes = filter(lambda x: x.isLeaf(), self.nodes.values())
        return set(map(lambda x: x.name, leafNodes))

    def moduleName(self, instPath: HierInstPath) -> Optional[str]:
        if instPath.instances.__len__() == 0:
            assert instPath.module in self.nodes
            return instPath.module

        node = self.nodes[instPath.module]
        for instanceName in instPath.instances:
            if node == None:
                break
            node = node.next.get(instanceName)
        if node is None:
            return None
        return node.name

    def forward(self, instPath: HierInstPath):
        if instPath.module in self.roots:
            return [instPath]
        # instPath is not from root
        res: list[HierInstPath] = []
        for pInst, pNode in self.nodes[instPath.module].prev.items():
            pInstPath = HierInstPath(pNode.name, (pInst,) + instPath.instances)
            subList = self.forward(pInstPath)
            res.extend(subList)
        return res

    def backward(self, instPath: HierInstPath) -> list[HierInstPath]:
        moduleName = self.moduleName(instPath)
        assert moduleName is not None
        if self.isLeaf(moduleName):
            return [instPath]
        # instPath is not leaf
        res: list[HierInstPath] = []
        for sInst, sNode in self.nodes[instPath.module].next.items():
            sInstPath = HierInstPath(sNode.name, instPath.instances + (sInst,))
            subList = self.backward(sInstPath)
            res.extend(subList)
        return res


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
