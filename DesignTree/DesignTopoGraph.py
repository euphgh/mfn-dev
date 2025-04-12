from DesignTree.Utils import HierInstPath, dictAdd, cl
from DesignTree.PortXml import PortXmlReader
from DesignTree.Node import ModuleNode, ModuleLink
from dataclasses import dataclass


@dataclass(frozen=True)
class InstParentPath:
    """
    <container> instantiates <subMoudle> with name <instance>
    """

    container: str
    instance: str
    subModule: str

    @staticmethod
    def fromStr(x: str) -> "InstParentPath":
        instPath, sModule = x.split(":")
        pModule, instance = instPath.split(".")
        return InstParentPath(pModule, instance, sModule)


class DesignTopoGraph:
    """
    Design hierarchical topological graph
    """

    def __init__(self) -> None:
        self.nodes = dict[str, ModuleNode]()
        self.roots = set[str]()

    def createModuleHier(
        self, containerNameList: list[str], instParentPaths: list[InstParentPath]
    ):
        for container in containerNameList:
            dictAdd(self.nodes, container, ModuleNode(container))
            self.roots.add(container)

        for p in instParentPaths:

            if p.container not in self.nodes:
                dictAdd(self.nodes, p.container, ModuleNode(p.container))
                self.roots.add(p.container)
                cl.warning(
                    f"logical/tile_info.xml Container List not cover instance parent path: {p.container}"
                )

            pModuleNode = self.nodes[p.container]
            # get value if key exist, else insert new value and return
            sModuleNode = self.nodes.setdefault(p.subModule, ModuleNode(p.subModule))

            # set double direct link
            dictAdd(pModuleNode.next, p.instance, sModuleNode)
            dictAdd(sModuleNode.prev, ModuleLink(p.container, p.instance), pModuleNode)

            if p.subModule in self.roots:
                self.roots.remove(p.subModule)

    def tops(self, modules: set[str]):
        """
        return a set of successfully selected top module
        """
        moduleSet = dict[str, ModuleNode]()
        success = set[str]()
        for top in modules:
            topNode = self.nodes.get(top)
            if topNode is None:
                continue
            success.add(top)
            queue = list[ModuleNode]()
            queue.append(topNode)
            while queue.__len__() > 0:
                currNode = queue.pop()
                moduleSet[currNode.name] = currNode
                for nextModule in currNode.next.values():
                    queue.append(self.nodes[nextModule.name])

        self.roots = success
        self.nodes = moduleSet
        return success

    def isLeaf(self, moduleName: str) -> bool:
        node = self.nodes.get(moduleName)
        if node is not None:
            return node.isLeaf()
        else:
            return False

    def containers(self) -> set[str]:
        containerNodes = filter(lambda x: not x.isLeaf(), self.nodes.values())
        return set(map(lambda x: x.name, containerNodes))

    def modules(self):
        return set(self.nodes.keys())

    def leaves(self) -> set[str]:
        leafNodes = filter(lambda x: x.isLeaf(), self.nodes.values())
        return set(map(lambda x: x.name, leafNodes))

    def moduleName(self, instPath: HierInstPath) -> str | None:
        if instPath.instances.__len__() == 0:
            assert instPath.module in self.nodes
            return instPath.module

        node = self.nodes[instPath.module]
        for instanceName in instPath.instances:
            if node is None:
                break
            node = node.next.get(instanceName)
        if node is None:
            return None
        return node.name

    def moduleNode(self, instPath: HierInstPath) -> ModuleNode | None:
        if instPath.instances.__len__() == 0:
            assert instPath.module in self.nodes
            return self.nodes[instPath.module]

        node = self.nodes[instPath.module]
        for instanceName in instPath.instances:
            if node is None:
                break
            node = node.next.get(instanceName)
        if node is None:
            return None
        return node

    def outer(self, instPath: HierInstPath):
        if instPath.module in self.roots:
            return [instPath]
        # instPath is not from root
        res: list[HierInstPath] = []
        for moduleLink, pNode in self.nodes[instPath.module].prev.items():
            pInstPath = HierInstPath(
                pNode.name, (moduleLink.instance,) + instPath.instances
            )
            subList = self.outer(pInstPath)
            res.extend(subList)
        return res

    def inner(self, instPath: HierInstPath) -> list[HierInstPath]:
        moduleName = self.moduleName(instPath)
        assert moduleName is not None
        if self.isLeaf(moduleName):
            return [instPath]
        # instPath is not leaf
        res: list[HierInstPath] = []
        for sInst, sNode in self.nodes[instPath.module].next.items():
            sInstPath = HierInstPath(sNode.name, instPath.instances + (sInst,))
            subList = self.inner(sInstPath)
            res.extend(subList)
        return res

    def createPortTopo(self, xmlDir: str):
        self.portXmls = PortXmlReader(xmlDir, self.containers())
        for module, node in self.nodes.items():
            if node.isLeaf():
                continue
            modulePortXml = self.portXmls.load(module, "port")
            assert modulePortXml is not None
            node.loadPortXml(modulePortXml)
            moduleLocalConnect = self.portXmls.load(module, "local_connect")
            assert moduleLocalConnect is not None
            node.loadLocalConnec(moduleLocalConnect)

    def instPathAdd(
        self, left: HierInstPath, right: HierInstPath
    ) -> HierInstPath | None:
        if self.moduleName(left) == right.module:
            return HierInstPath(left.module, left.instances + right.instances)
        else:
            return None

    def instPathSub(
        self, left: HierInstPath, right: HierInstPath
    ) -> HierInstPath | None:
        if left.module != right.module:
            return None
        if left.instances.__len__() <= right.instances.__len__():
            return None
        for i in range(right.instances.__len__()):
            if left.instances[i] != right.instances[i]:
                return None
        subModuleName = self.moduleName(left)
        if subModuleName is None:
            return None
        return HierInstPath(subModuleName, left.instances[right.instances.__len__() :])
