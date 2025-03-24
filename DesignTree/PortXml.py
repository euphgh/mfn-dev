from DesignTree.Utils import PortDir, HierInstPath
from xml.etree.ElementTree import ElementTree as XmlDoc
from xml.etree.ElementTree import Element
from xml.etree import ElementTree as ET
from typing import Optional
import os


# data struct for end_block in PortXml
# <end_block block_inst_name="uvpep" block_class_name="vpep" port_name="DBUS_VPEP_daisychain" port_signal_name="DBUS_VPEP_daisychain_data" port_signal_dir="input" port_dir="receive"/>
class EndBlock:
    def __init__(self) -> None:
        self.rInstPath = HierInstPath.empty()
        self.moduleName = str()
        self.portBundle = str()
        self.portSignal = str()
        self.dir: PortDir = PortDir.EMPTY


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


# data struct for Bundle element in PortXml
class BundleConnec:
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.wireList = list[WireConnec]()


class PortXmlParser:
    def __init__(self, portXml: XmlDoc, moduleName: str) -> None:
        self.xmlDoc: XmlDoc = portXml
        root = portXml.getroot()
        self.bundleDict = dict[str, BundleConnec]()
        self.wireDict = dict[str, WireConnec]()
        for bundleElem in root.findall("bundle"):
            assert isinstance(bundleElem, Element)
            bc = BundleConnec(bundleElem.attrib["name"])
            self.bundleDict[bc.name] = bc
            for wireElem in bundleElem.findall("wire"):
                wc = WireConnec(wireElem.attrib["name"])
                self.wireDict[wc.name] = wc
                wc.range = (
                    int(wireElem.attrib["high_bit"]),
                    int(wireElem.attrib["low_bit"]),
                )
                for endBlockElem in wireElem.findall("end_block"):
                    eb = EndBlock()
                    eb.rInstPath = HierInstPath(
                        endBlockElem.attrib["block_inst_name"], False
                    )
                    eb.moduleName = endBlockElem.attrib["block_class_name"]
                    eb.portBundle = endBlockElem.attrib["port_name"]
                    eb.portSignal = endBlockElem.attrib["port_signal_name"]
                    eb.dir = PortDir.fromStr(endBlockElem.attrib["port_dir"])
                    if eb.moduleName == moduleName:
                        wc.outer = eb
                    else:
                        wc.inners.append(eb)
                bc.wireList.append(wc)

    def findByBundle(self, name: str) -> Optional[BundleConnec]:
        return self.bundleDict.get(name, None)

    def findByWire(self, name: str) -> Optional[WireConnec]:
        return self.wireDict.get(name, None)


class PortXmlReader:
    def __init__(self, portXmlDir: str) -> None:
        self.dirName: str = portXmlDir
        # get all *_xml.port name from xml dir, consistent a set "fileList"
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
