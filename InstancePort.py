from enum import Enum

class PortDir(Enum):
    INPUT = 1
    OUTPUT = 2
    INOUT = 3

LeafModuleSet:set[str]

class PortXmlReader:
    @staticmethod
    def loadPortXml(file:str):
        pass

    @staticmethod
    def fillPortConnec(instancePort: "InstancePort"):
        pass

class InstanceModuleMap:
    @staticmethod
    def moduleName(instanceName: str):
        pass

class InstancePort:
    def __init__(self, instanceName:str = "", moduleName:str = "", portName:str = "", dir: PortDir = PortDir.INPUT) -> None:
        self.instanceName:str = instanceName
        self.moduleName:str = moduleName
        self.portName:str = portName
        self.dir:PortDir = dir
        self.isLeaf:bool = moduleName in LeafModuleSet
        self.portConnec:list[InstancePort] = []
        PortXmlReader.fillPortConnec(self)
        

    def __eq__(self, other)->bool:
        if isinstance(other, InstancePort):
            return self.instanceName == other.instanceName and self.portName == other.portName
        return False

    def __hash__(self):
        return hash(self.instanceName + self.portName)

    def leaves(self)->list["InstancePort"]:
        return []
    def __str__(self) -> str:
        return ""

if __name__ == "__main__":
    InstancePort("")