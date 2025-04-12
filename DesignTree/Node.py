from DesignTree.Utils import HierInstPath, WireRange, dictAdd, cl
from DesignTree.PortXml import PortXmlParser, WireConnec, EndBlock
from typing import Optional
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModuleLink:
    container: str
    instance: str


class ModuleNode:
    """
    Node of Hierarchical Tree

    self.name: module name
    self.next: name of instance in the module -> inner module node
    self.prev: instance name of self in the outer module -> outer module node
    """

    def __init__(self, name: str) -> None:
        self.name: str = name
        # sub instance name -> module node
        self.next = dict[str, ModuleNode]()
        # parent module name + self instance name -> module node
        self.prev = dict[ModuleLink, ModuleNode]()
        # port name -> port node
        self.ports = dict[str, PortWireNode]()
        # local connect: wire name -> instance name, port node
        self.local = dict[str, list[tuple[str, PortWireNode]]]()
        # bundle name to wire name set
        self.bundle2wire = dict[str, set[str]]()

    def isLeaf(self):
        return self.next.__len__() == 0

    def __getOrInsertPortNode(self, endBlock: EndBlock, wireRange: WireRange):
        """
        get the port node if the port of end block is exist in self.ports
        else new and insert a port node to self.ports and return it.
        """
        portName = endBlock.portWireName
        portNode = self.ports.get(portName)
        if portNode is not None:
            assert portNode.dir == endBlock.wireDir
            assert portNode.range == wireRange
            assert portNode.module == self
        else:
            portNode = PortWireNode(endBlock, wireRange, self)
            self.ports[portName] = portNode
        return portNode

    def doubleLink(
        self,
        wireConnec: WireConnec,
        iInstName: str,
        jInstName: str,
        iPortNode: "PortWireNode",
        jPortNode: "PortWireNode",
    ):
        # double link port node
        bundleConnec = wireConnec.bundleLink
        assert bundleConnec is not None
        i2j = WireLink(
            self.name,
            iInstName,
            jInstName,
            jPortNode.name,
            wireConnec.name,
            bundleConnec.name,
        )
        j2i = WireLink(
            self.name,
            jInstName,
            iInstName,
            iPortNode.name,
            wireConnec.name,
            bundleConnec.name,
        )
        return (i2j, j2i)

    def loadPortXml(self, portXml: PortXmlParser):
        for bundleName, bundleConnec in portXml.bundleDict.items():
            wireNameSet = {wire for wire in bundleConnec.wires.keys()}
            dictAdd(self.bundle2wire, bundleName, wireNameSet)

            for wireName, wireConnec in bundleConnec.wires.items():
                # endblock with module name equal to self name
                selfEndBlock = wireConnec.endBlockOf(self.name)
                assert selfEndBlock is not None
                # basic assumption
                assert selfEndBlock.portWireName == wireName
                assert selfEndBlock.portBundleName == bundleName

                selfPort = self.__getOrInsertPortNode(selfEndBlock, wireConnec.range)

                # travel other end block to link self port and inner port
                for innerEndBlock in wireConnec.endBlocks:
                    # skil self end block
                    if innerEndBlock == selfEndBlock:
                        continue

                    # new inner port node
                    subModuleNode = self.next[innerEndBlock.instName]
                    # if innerEndBlock.portWireName not exist, create a new port node, new PortWireNode
                    innerPort = subModuleNode.__getOrInsertPortNode(
                        innerEndBlock, wireConnec.range
                    )

                    forward, backward = self.doubleLink(
                        wireConnec,
                        "",
                        innerEndBlock.instName,
                        selfPort,
                        innerPort,
                    )
                    assert selfPort.module is not None
                    assert innerPort.module is not None
                    dictAdd(selfPort.inner, forward, innerPort)
                    dictAdd(innerPort.outer, backward, selfPort)

    def loadLocalConnec(self, localConnect: PortXmlParser):
        for bundleName, bundleConnec in localConnect.bundleDict.items():
            wireNameSet = {wire for wire in bundleConnec.wires.keys()}
            dictAdd(self.bundle2wire, bundleName, wireNameSet)

            for wireName, wireConnec in bundleConnec.wires.items():
                # (instance name, port node)
                portNodeList = list[tuple[str, PortWireNode]]()
                for endBlock in wireConnec.endBlocks:
                    # new inner port node
                    subModuleNode = self.next.get(endBlock.instName)
                    # In normal status, module nodes are created when load info yaml
                    # if not found, create a new leaf block
                    if subModuleNode is None:
                        subModuleNode = ModuleNode(endBlock.moduleName)
                        self.next[endBlock.instName] = subModuleNode
                        moduleLink = ModuleLink(self.name, endBlock.instName)
                        subModuleNode.prev[moduleLink] = self
                        cl.warning(
                            f"Not found module {endBlock.moduleName} in info.yaml"
                        )
                    portNode = PortWireNode(endBlock, wireConnec.range, subModuleNode)
                    portNode = subModuleNode.__getOrInsertPortNode(
                        endBlock, wireConnec.range
                    )
                    portNodeList.append((endBlock.instName, portNode))

                for i in range(portNodeList.__len__()):
                    iInstName, iPortNode = portNodeList[i]
                    for j in range(i + 1, portNodeList.__len__()):
                        jInstName, jPortNode = portNodeList[j]
                        forward, backward = self.doubleLink(
                            wireConnec,
                            iInstName,
                            jInstName,
                            iPortNode,
                            jPortNode,
                        )
                        assert iPortNode.module is not None
                        assert jPortNode.module is not None
                        dictAdd(iPortNode.outer, forward, jPortNode)
                        dictAdd(jPortNode.outer, backward, iPortNode)

                dictAdd(self.local, wireName, portNodeList)

    def portOf(self, bundle: str):
        """
        return None if bundle is not found in this module
        else return a list of PortWireNode of this Module's port
        """
        wireSet = self.bundle2wire.get(bundle)
        if wireSet is not None:
            res = list[PortWireNode]()
            for wireName in wireSet:
                portNode = self.ports.get(wireName)
                if portNode is not None:
                    res.append(portNode)
            return res
        return None

    def localOf(self, bundle: str):
        wireSet = self.bundle2wire.get(bundle)
        if wireSet is not None:
            res = list[tuple[str, PortWireNode]]()
            for wireName in wireSet:
                localList = self.local.get(wireName)
                if localList is not None:
                    res.extend(map(lambda x: x, localList))
            return res
        return None


@dataclass(frozen=True)
class WireLink:
    container: str
    # if is container port, it should be sub instance name
    thisInst: str
    # for outer
    thatInst: str
    port: str
    wire: str = field(compare=False)
    bundle: str = field(compare=False)


class PortWireNode:
    """
    Node for Hierarchy Port Tree
    """

    def __init__(
        self, endBlock: EndBlock, wireRange: WireRange, moduleNode: ModuleNode
    ) -> None:
        self.dir = endBlock.wireDir
        self.name = endBlock.portWireName
        self.range = wireRange
        self.module: ModuleNode | None = moduleNode
        # sub instance name + port name -> port node
        self.inner = dict[WireLink, PortWireNode]()
        # parent instance name + port name -> port node
        # include peers and parents
        self.outer = dict[WireLink, PortWireNode]()

    def leaves(
        self, instPath: HierInstPath
    ) -> list[tuple[HierInstPath, "PortWireNode"]]:
        if self.inner.__len__() == 0:
            return [(instPath, self)]
        res = list[tuple[HierInstPath, "PortWireNode"]]()
        for link, node in self.inner.items():
            res.extend(node.leaves(instPath.addInst(link.thatInst)))
        return res
