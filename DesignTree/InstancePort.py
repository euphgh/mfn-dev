from DesignTree.Utils import PortDir, HierInstPath
import os
from xml.etree.ElementTree import ElementTree as XmlDoc
from xml.etree import ElementTree as ET
from typing import Optional
import yaml

class PortXmlReader:
    def __init__(self, portXmlDir:str) -> None:
        self.dirName:str = portXmlDir
        # get all *_xml.port name from xml dir, consistent a set "fileList"
        portXmlList:list[str] = [file.name[:-9] for file in os.scandir(portXmlDir) if file.is_file() and file.name.endswith("_port.xml")]
        self.fileList:set[str] = set(portXmlList)
        self.xmlDict:dict[str, XmlDoc] = {}

    def __getitem__(self, moduleName:str)-> Optional[XmlDoc]:
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
                self.xmlDict[moduleName] = tree
                self.xmlDict.get
                return tree
        else:
            return None

# data struct for end_block in PortXml
# <end_block block_inst_name="uvpep" block_class_name="vpep" port_name="DBUS_VPEP_daisychain" port_signal_name="DBUS_VPEP_daisychain_data" port_signal_dir="input" port_dir="receive"/>
class EndBlock:
    def __init__(self) -> None:
        self.instPath: HierInstPath # module name can be searched by instPath
        self.portBundle:str
        self.portSignal:str
        self.dir:PortDir = PortDir.INPUT

# data struct for wire element in PortXml
# <wire name="PERFMON_CAC_SelfRefClks_p1_active" high_bit="0" low_bit="0">
# 	<end_block block_inst_name="umc" block_class_name="umc" port_name="PERFMON_CAC_SelfRefClks_p1" port_signal_name="PERFMON_CAC_SelfRefClks_p1_active" port_signal_dir="output" port_dir="transmit"/>
# 	<end_block block_inst_name="umcdat" block_class_name="umcdat" port_name="PERFMON_CAC_SelfRefClks_p1" port_signal_name="PERFMON_CAC_SelfRefClks_p1_active" port_signal_dir="output" port_dir="transmit"/>
# </wire>
class WireConnec:
    def __init__(self) -> None:
        self.wireName:str = ""
        self.range:tuple[int, int] = (0, 0)
        self.outer:EndBlock         # module port
        self.inners:list[EndBlock]  # ports of instance in this module, connect to outer

# data struct for Bundle element in PortXml
class BundleConnec:
    def __init__(self) -> None:
        self.bundleName: str = ""
        self.wireList:list[WireConnec] = []

class PortXmlParser:
    def __init__(self, portXml: XmlDoc) -> None:
        self.xmlDoc:XmlDoc = portXml
        root = portXml.getroot()
        bundleElements = root.findall("bundle")
    
class InstanceModuleMap:
    def __init__(self, yamlFile:str) -> None:
        self.instPath2Module:dict[HierInstPath, str] = {}
        # yaml file example: <instance path>:<module name>
        # ALL_BLOCK_INSTANCE_PARENT_PATH:
        #   - dchub.dchubbubl:dchubbubl_wrapper
        #   - dchub.dchubbubmem0:dchubbubmem_wrapper
        with open(yamlFile, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            assert isinstance(data, dict)
            assert "ALL_BLOCK_INSTANCE_PARENT_PATH" in data
            for pair in data["ALL_BLOCK_INSTANCE_PARENT_PATH"]:
                assert isinstance(pair, str)
                instPathStr, moduleName = pair.split(":")
                self.instPath2Module[HierInstPath(instPathStr)] = moduleName

    def __getitem__(self, instPath: HierInstPath)-> Optional[str]:
        return self.instPath2Module.get(instPath, None)
    
    def __str__(self) -> str:
        return self.instPath2Module.__str__()

class InstancePort:
    def __init__(self, 
                 instPath:HierInstPath,
                 moduleName:str, 
                 portName:str, 
                 dir: PortDir,
                 isLeaf: bool,
                 connec: list["InstancePort"]
                 ) -> None:
        self.instPath:HierInstPath = instPath
        self.moduleName:str = moduleName
        self.portName:str = portName
        self.dir:PortDir = dir
        self.isLeaf:bool = isLeaf
        self.connec:list["InstancePort"] = connec
        
    def __eq__(self, other:object)->bool:
        if isinstance(other, InstancePort):
            return self.instPath == other.instPath and self.portName == other.portName
        return False

    def __hash__(self):
        return hash(self.instPath.__str__() + self.portName)

    def leaves(self)->list["InstancePort"]:
        return []

    def __str__(self) -> str:
        return ""
