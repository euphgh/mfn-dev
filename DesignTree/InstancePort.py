from DesignTree.Utils import HierInstPath, PortDir, WireRange
from DesignTree.HierTree import ModuleNode
from typing import Optional
from xml.etree.ElementTree import ElementTree as XmlDoc
from xml.etree.ElementTree import Element

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


class PortWireNode:
    """
    Node for Hierarchy Port Tree
    """

    def __init__(self) -> None:
        self.name = str()  # wire element attrib name
        self.bundle = str()  # bundle element attrib name
        self.range = WireRange()
        self.portSignalName = str()  # port wire name
        self.portName = str()  # port bundle name
        self.wireDir = PortDir.EMPTY
        self.bundleDir = PortDir.EMPTY
        self.module: Optional[ModuleNode] = None
        # instance name + port name
        self.inner = dict[str, PortSet]()
        self.outer = dict[str, PortSet]()


class PortSet:
    """
    all port of a module
    a pointer of module node
    """

    def __init__(self) -> None:
        self.nodes = dict[str, PortWireNode]()

    def loadPortXml(self, xml: XmlDoc) -> None:
        pass

    def wireOf(self, name: str) -> Optional[PortWireNode]:
        return self.nodes.get(name)

    def bundleOf(self, bundle: str) -> list[PortWireNode]:
        return list(filter(lambda x: x.portName == bundle, self.nodes.values()))


class PortManager:
    def __init__(self) -> None:
        # module name -> PortSet
        self.portSetDict = dict[str, PortSet]()

    def loadPortXml(self, module: ModuleNode, xml: XmlDoc):
        containerName = xml.getroot().attrib["container"]
        assert containerName == module.name
        portSet = PortSet()
        root = xml.getroot()

        for bundleElem in root.findall("bundle"):
            assert isinstance(bundleElem, Element)
            bundle = bundleElem.attrib["name"]
            for wireElem in bundleElem.findall("wire"):
                portWireNode = PortWireNode()
                portWireNode.name = wireElem.attrib["name"]
                portWireNode.bundle = bundle
                portWireNode.range = WireRange(
                    int(wireElem.attrib["high_bit"]),
                    int(wireElem.attrib["low_bit"]),
                )
                for endBlockElem in wireElem.findall("end_block"):
                    blockInstName = endBlockElem.attrib["block_inst_name"]
                    blockClassName = endBlockElem.attrib["block_class_name"]
                    portName = endBlockElem.attrib["port_name"]
                    portSignalName = endBlockElem.attrib["port_signal_name"]
                    portSignalDir = PortDir.fromStr(
                        endBlockElem.attrib["port_signal_dir"]
                    )
                    portDir = PortDir.fromStr(endBlockElem.attrib["port_dir"])
                    if blockClassName == module.name:
                        portWireNode.bundleDir = portDir
                        portWireNode.wireDir = portSignalDir
                        portWireNode.module = module
                        portWireNode.portSignalName = portSignalName
                        portWireNode.portName = portName
                    else:
                        subPortSet = self.portSetDict.setdefault(
                            blockClassName, PortSet()
                        )
                        portWireNode.inner[blockInstName] = subPortSet
