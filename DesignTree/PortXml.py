"""
建模连接关系

模块建模: read logical_info.yml, self port.xml and local_connect.xml not recursively
module name
module inner:  内部模块的实例化名称 -> 子模块节点
module outer:  (父模块名称 + 实例化名称) -> 父模块节点 -> 父模块端口 (记录连接的wire的名称，wire名称可能同名，同名则表示fanout)
ports: a set of port node, distinguish by port name
locals: (instance name/port name, instance name/port name) -> wire name and more information

端口建模:
port name
inner:  内部模块的实例化名称 -> 子模块节点 -> 子模块端口名 -> 子模块端口节点
        记录连接的wire的名称，wire名称可能同名，同名则表示fanout
outer:  (父模块名称 + 实例化名称) -> 父模块节点 -> 父模块端口
pears:  模块内相互连接, (父模块名称 + 实例化名称) -> 父模块节点 -> 内部模块实例化名称 -> 子模块端口名 -> 子模块端口节点

port_signal_name: 端口名
"""

from DesignTree.Utils import PortDir, cl, WireRange, dictAdd
from xml.etree.ElementTree import ElementTree as XmlDoc
from xml.etree.ElementTree import Element
from xml.etree import ElementTree as ET
from typing import Optional, TypeAlias
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
    def __init__(self, name: str, msb: int, lsb: int) -> None:
        self.name: str = name
        self.range = WireRange(msb, lsb)
        self.endBlocks = list[EndBlock]()
        self.bundleLink: Optional[BundleConnec] = None  # back link

    def endBlockOf(self, moduleName: str):
        for eb in self.endBlocks:
            if eb.moduleName == moduleName:
                return eb
        return None

    def __str__(self) -> str:
        return f"{self.name}:{self.range}"


class BundleConnec:
    """
    Data struct for Bundle element in PortXml
    """
    def __init__(self, name: str) -> None:
        # not equal to port_name(port interface name) of end_block
        self.name: str = name
        # wire name -> WireConnec
        self.wires = dict[str, WireConnec]()

    def __str__(self) -> str:
        return f"{self.name}"


class PortXmlParser:
    """
    Only one assumption
    bundle name and wire name is unique
    """

    def __init__(self, portXml: XmlDoc, moduleName: str) -> None:
        root = portXml.getroot()
        assert root.attrib["container"] == moduleName
        self.bundleDict = dict[str, BundleConnec]()
        self.wireDict = dict[str, WireConnec]()
        for bundleElem in root.findall("bundle"):
            assert isinstance(bundleElem, Element)
            bundleConnec = BundleConnec(bundleElem.attrib["name"])
            dictAdd(self.bundleDict, bundleConnec.name, bundleConnec)
            for wireElem in bundleElem.findall("wire"):
                wireConnec = WireConnec(
                    name=wireElem.attrib["name"],
                    msb=int(wireElem.attrib["high_bit"]),
                    lsb=int(wireElem.attrib["low_bit"]),
                )
                dictAdd(self.wireDict, wireConnec.name, wireConnec)
                wireConnec.bundleLink = bundleConnec  # set link of bundleConnec
                for endBlockElem in wireElem.findall("end_block"):
                    endBlock = EndBlock()
                    endBlock.instName = endBlockElem.attrib["block_inst_name"]
                    endBlock.moduleName = endBlockElem.attrib["block_class_name"]
                    endBlock.portBundleName = endBlockElem.attrib["port_name"]
                    endBlock.portWireName = endBlockElem.attrib["port_signal_name"]
                    if endBlock.portBundleName == "" or endBlock.portWireName == "":
                        cl.warning(
                            f"skip {moduleName}_port/local_connect.xml bundle {bundleConnec.name}'s wire {wireConnec.name} empty endBlock"
                        )
                        continue
                    # direction
                    endBlock.wireDir = PortDir.fromStr(
                        endBlockElem.attrib["port_signal_dir"]
                    )
                    endBlock.bundleDir = PortDir.fromStr(
                        endBlockElem.attrib["port_dir"]
                    )
                    # set link of bundleConnec
                    endBlock.wireLink = wireConnec
                    wireConnec.endBlocks.append(endBlock)

                dictAdd(bundleConnec.wires, wireConnec.name, wireConnec)


def scanFileFrom(dir: str, suffix: str):
    return {
        file.name[: -suffix.__len__()]
        for file in os.scandir(dir)
        if file.is_file() and file.name.endswith(suffix)
    }


# module name -> port.xml or local_connnect.xml
moduleXmlMap: TypeAlias = dict[str, PortXmlParser]


class PortXmlReader:
    def __init__(self, portXmlDir: str, containerSet: set[str]) -> None:
        self.dirName: str = portXmlDir
        # get all *_port.xml from xml dir, consistent a set
        portXmlSet = scanFileFrom(portXmlDir, "_port.xml")
        # get all *_local_connect.xml from xml dir, consistent a set
        localConnectSet = scanFileFrom(portXmlDir, "_local_connect.xml")

        for container in containerSet:
            if container not in portXmlSet:
                cl.warning(f"miss {container}_port.xml in {portXmlDir}")
            if container not in localConnectSet:
                cl.warning(f"miss {container}_local_connect.xml in {portXmlDir}")

        self.containerSet = containerSet

        # xml suffix name(port or local_connect) -> moduleDict
        self.xmls = {
            "port": moduleXmlMap(),
            "local_connect": moduleXmlMap(),
        }

    def __fromModuleDict(self, moduleName: str, suffix: str) -> Optional[PortXmlParser]:
        d = self.xmls[suffix]
        # module name is valid
        if moduleName in self.containerSet:
            # module name is cached in dict
            if moduleName in d:
                return d[moduleName]
            # load xml when needed
            else:
                tree: XmlDoc = ET.parse(f"{self.dirName}/{moduleName}_{suffix}.xml")
                parser = PortXmlParser(tree, moduleName)
                dictAdd(d, moduleName, parser)
                return parser
        else:
            return None

    def load(self, moduleName: str, suffix: str) -> Optional[PortXmlParser]:
        assert suffix == "port" or suffix == "local_connect"
        return self.__fromModuleDict(moduleName, suffix)
