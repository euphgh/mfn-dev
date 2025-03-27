from DesignTree.Utils import PortDir, cl
from DesignTree.InstancePort import PortSet, PortWireNode
from xml.etree.ElementTree import ElementTree as XmlDoc
from xml.etree.ElementTree import Element
from xml.etree import ElementTree as ET
from typing import Optional
import os


class EndBlock:
    """
    Data struct for end_block in PortXml

    <end_block block_inst_name="uvpep" block_class_name="vpep"
        port_name="DBUS_VPEP_daisychain"
        port_signal_name="DBUS_VPEP_daisychain_data"
        port_signal_dir="input"
        port_dir="receive"/>
    """
    def __init__(self) -> None:
        self.instName: str
        self.moduleName = str()
        self.portBundleName = str()
        self.portWireName = str()
        self.wireDir: PortDir = PortDir.EMPTY  # port_signal_dir
        self.bundleDir: PortDir = PortDir.EMPTY  # port_dir
        self.wireLink: Optional[WireConnec] = None  # back link

    def __str__(self) -> str:
        return f"{self.instName}:{self.moduleName}:{self.portWireName}({self.wireDir}):{self.portBundleName}({self.bundleDir})"


class WireConnec:
    """
    Data struct for wire element in PortXml

    <wire name="PERFMON_CAC_SelfRefClks_p1_active" high_bit="0" low_bit="0">
            <end_block block_inst_name="umc" block_class_name="umc"
                port_signal_name="PERFMON_CAC_SelfRefClks_p1_active" .../>
            <end_block ... />
            <end_block ... />
    </wire>
    """
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.range = tuple[int, int]()
        self.outer = EndBlock()  # module port
        # ports of instance in this module, connect to outer
        self.inners = list[EndBlock]()
        self.bundleLink: Optional[BundleConnec] = None  # back link

    def __str__(self) -> str:
        return f"{self.name}:{self.range}"


class BundleConnec:
    """
    Data struct for Bundle element in PortXml
    """
    def __init__(self, name: str) -> None:
        # not equal to port_name(port interface name) of end_block
        self.name: str = name
        self.wireList = list[WireConnec]()
        self.dir = PortDir.EMPTY  # bundle dir, in transmition level

    def __str__(self) -> str:
        return f"{self.name}:{self.dir}"


class PortXmlParser:

    def __init__(self, portXml: XmlDoc, moduleName: str) -> None:
        self.xmlDoc: XmlDoc = portXml
        root = portXml.getroot()
        self.bundleDict = dict[str, BundleConnec]()
        self.wireDict = dict[str, WireConnec]()
        for bundleElem in root.findall("bundle"):
            assert isinstance(bundleElem, Element)
            bundleConnec = BundleConnec(bundleElem.attrib["name"])
            self.bundleDict[bundleConnec.name] = bundleConnec
            bundleDirect = set[PortDir]()
            for wireElem in bundleElem.findall("wire"):
                wireConnec = WireConnec(wireElem.attrib["name"])
                self.wireDict[wireConnec.name] = wireConnec
                wireConnec.range = (
                    int(wireElem.attrib["high_bit"]),
                    int(wireElem.attrib["low_bit"]),
                )
                wireConnec.bundleLink = bundleConnec  # set link of bundleConnec
                endBlockDirect = set[PortDir]()
                for endBlockElem in wireElem.findall("end_block"):
                    endBlock = EndBlock()
                    endBlock.instName = endBlockElem.attrib["block_inst_name"]
                    endBlock.moduleName = endBlockElem.attrib["block_class_name"]
                    endBlock.portBundleName = endBlockElem.attrib["port_name"]
                    endBlock.portWireName = endBlockElem.attrib["port_signal_name"]
                    # direction
                    portWireDir = PortDir.fromStr(
                        endBlockElem.attrib["port_signal_dir"]
                    )
                    bundleDirect.add(PortDir.fromStr(endBlockElem.attrib["port_dir"]))
                    endBlock.wireDir = portWireDir
                    endBlockDirect.add(portWireDir)
                    # set link of bundleConnec
                    endBlock.wireLink = wireConnec
                    # outer and inners
                    if endBlock.moduleName == moduleName:
                        wireConnec.outer = endBlock
                    else:
                        wireConnec.inners.append(endBlock)
                cl.warn_if(
                    endBlockDirect.__len__() != 1,
                    f"port_signal_dir diff in {moduleName}_port.xml wire {wireConnec.name}",
                )
                bundleConnec.wireList.append(wireConnec)
            cl.warn_if(
                bundleDirect.__len__() != 1,
                f"port_dir diff in {moduleName}_port.xml bundle {bundleConnec.name}",
            )
            bundleConnec.dir = bundleDirect.pop()

    def findByBundle(self, name: str) -> Optional[BundleConnec]:
        return self.bundleDict.get(name, None)

    def findByWire(self, name: str) -> Optional[WireConnec]:
        return self.wireDict.get(name, None)


class PortXmlReader:

    def __init__(self, portXmlDir: str, containerSet: set[str]) -> None:
        self.dirName: str = portXmlDir
        # get all *_xml.porbidirectt name from xml dir, consistent a set
        portXmlSet = set(
            [
                file.name[:-9]
                for file in os.scandir(portXmlDir)
                if file.is_file() and file.name.endswith("_port.xml")
            ]
        )

        for container in containerSet:
            if container not in portXmlSet:
                cl.warning(f"miss {container}_port.xml in {portXmlDir}")

        self.containerSet = containerSet
        self.xmlDict: dict[str, XmlDoc] = {}

    def __getitem__(self, moduleName: str) -> Optional[XmlDoc]:
        # module name is valid
        if moduleName in self.containerSet:
            # module name is cached in dict
            if moduleName in self.xmlDict:
                return self.xmlDict[moduleName]
            # load xml when needed
            else:
                tree: XmlDoc = ET.parse(f"{self.dirName}/{moduleName}_port.xml")
                self.xmlDict[moduleName] = tree
                return tree
        else:
            return None
