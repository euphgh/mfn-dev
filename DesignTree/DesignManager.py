from DesignTree.Utils import PortDir, HierInstPath
from DesignTree.InstancePort import *

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