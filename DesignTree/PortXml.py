from DesignTree.Utils import PortDir, HierInstPath
from xml.etree.ElementTree import ElementTree as XmlDoc
from xml.etree.ElementTree import Element
from xml.etree import ElementTree as ET
from typing import Optional
import os
import sys


# data struct for end_block in PortXml
# <end_block block_inst_name="uvpep" block_class_name="vpep" port_name="DBUS_VPEP_daisychain" port_signal_name="DBUS_VPEP_daisychain_data" port_signal_dir="input" port_dir="receive"/>
class EndBlock:
    def __init__(self) -> None:
        self.rInstPath = HierInstPath.empty()
        self.moduleName = str()
        self.portBundleName = str()
        self.portWireName = str()
        self.dir: PortDir = PortDir.EMPTY  # wire direct
        self.wireLink: Optional[WireConnec] = None  # back link


# data struct for wire element in PortXml
# <wire name="PERFMON_CAC_SelfRefClks_p1_active" high_bit="0" low_bit="0">
# 	<end_block block_inst_name="umc" block_class_name="umc" port_name="PERFMON_CAC_SelfRefClks_p1" port_signal_name="PERFMON_CAC_SelfRefClks_p1_active" port_signal_dir="output" port_dir="transmit"/>
# 	<end_block block_inst_name="umcdat" block_class_name="umcdat" port_name="PERFMON_CAC_SelfRefClks_p1" port_signal_name="PERFMON_CAC_SelfRefClks_p1_active" port_signal_dir="output" port_dir="transmit"/>
# </wire>
class WireConnec:
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.range = tuple[int, int]()
        self.outer = EndBlock()  # module port
        # ports of instance in this module, connect to outer
        self.inners = list[EndBlock]()
        self.bundleLink: Optional[BundleConnec] = None  # back link


# data struct for Bundle element in PortXml
class BundleConnec:
    def __init__(self, name: str) -> None:
        # not equal to port_name(port interface name) of end_block
        self.name: str = name
        self.wireList = list[WireConnec]()
        self.dir = PortDir.EMPTY  # bundle dir, in transmition level


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
                    endBlock.rInstPath = HierInstPath(
                        endBlockElem.attrib["block_inst_name"], False
                    )
                    endBlock.moduleName = endBlockElem.attrib["block_class_name"]
                    endBlock.portBundleName = endBlockElem.attrib["port_name"]
                    endBlock.portWireName = endBlockElem.attrib["port_signal_name"]
                    # direction
                    portWireDir = PortDir.fromStr(
                        endBlockElem.attrib["port_signal_dir"]
                    )
                    bundleDirect.add(PortDir.fromStr(endBlockElem.attrib["port_dir"]))
                    endBlock.dir = portWireDir
                    endBlockDirect.add(portWireDir)
                    # set link of bundleConnec
                    endBlock.wireLink = wireConnec
                    # outer and inners
                    if endBlock.moduleName == moduleName:
                        wireConnec.outer = endBlock
                    else:
                        wireConnec.inners.append(endBlock)
                # TODO: assert
                if endBlockDirect.__len__() != 1:
                    print(
                        f"Warn: port_signal_dir diff in {moduleName}_port.xml wire {wireConnec.name}",
                        file=sys.stderr,
                    )
                bundleConnec.wireList.append(wireConnec)
            # TODO: assert
            if bundleDirect.__len__() != 1:
                print(
                    f"Warn: port_dir diff in {moduleName}_port.xml bundle {bundleConnec.name}",
                    file=sys.stderr,
                )
            bundleConnec.dir = bundleDirect.pop()

    def findByBundle(self, name: str) -> Optional[BundleConnec]:
        return self.bundleDict.get(name, None)

    def findByWire(self, name: str) -> Optional[WireConnec]:
        return self.wireDict.get(name, None)


class PortXmlReader:
    def __init__(self, portXmlDir: str) -> None:
        self.dirName: str = portXmlDir
        # get all *_xml.porbidirectt name from xml dir, consistent a set "fileList"
        portXmlList: list[str] = [
            file.name[:-9]
            for file in os.scandir(portXmlDir)
            if file.is_file() and file.name.endswith("_port.xml")
        ]
        self.fileList: set[str] = set(portXmlList)
        self.xmlDict: dict[str, PortXmlParser] = {}

    def __getitem__(self, moduleName: str) -> Optional[PortXmlParser]:
        # module name is valid
        if moduleName in self.fileList:
            # module name is cached in dict
            if moduleName in self.xmlDict:
                return self.xmlDict[moduleName]
            # load xml when needed
            else:
                tree: XmlDoc = ET.parse(f"{self.dirName}/{moduleName}_port.xml")
                containerName = tree.getroot().attrib["container"]
                assert isinstance(containerName, str)
                assert containerName == moduleName
                parser = PortXmlParser(tree, moduleName)
                self.xmlDict[moduleName] = parser
                return parser
        else:
            return None
