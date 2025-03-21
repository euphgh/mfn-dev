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

class DesignManager:
    def __init__(self, yamlFile:str, xmlDir:str) -> None:
        self.instPath2Module = InstanceModuleMap(yamlFile)
        self.portXmls = PortXmlReader(xmlDir)
        self.portSet: set[InstancePort]
        self.leafModuleSet:set[str]
    
    def xmlDocOf(self, id: HierInstPath|str)-> Optional[XmlDoc]:
        if isinstance(id, HierInstPath):
            moduleName = self.instPath2Module[id]
            if (moduleName == None): return None
            return self.portXmls[moduleName]
        else: # id is str
            return self.portXmls[id]

    def fillPortConnec(self, instPath:HierInstPath, moduleName:str, dir:PortDir, isLeaf: bool)-> list[InstancePort]:
        if (isLeaf): return []
        tree = self.xmlDocOf(moduleName)
        assert tree is not None
        # assumpt bia log port name is same with bundle name, not wire name
        # one bundle only have one wire and bundle name is same with wire name
        rootEle = tree.getroot()
        rootEle.find("")
        return []
    
    def addInstancePort(self, instPathStr:str, portName:str , dir: PortDir)->Optional[InstancePort]:
        instPath:HierInstPath = HierInstPath(instPathStr)
        moduleName = self.instPath2Module[instPath]
        if moduleName == None:
            return None
        isLeaf:bool = moduleName in self.leafModuleSet
        connec:list[InstancePort] = self.fillPortConnec(instPath, moduleName, dir, isLeaf)
        instancePort = InstancePort(instPath, moduleName, portName, dir, isLeaf, connec)
        self.portSet.add(instancePort)
        return instancePort
