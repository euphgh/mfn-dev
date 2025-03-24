from DesignTree.Utils import PortDir, HierInstPath
from DesignTree.InstancePort import *
from DesignTree.PortXml import *


class DesignManager:

    def __init__(self, yamlFile: str, xmlDir: str, leafListFile: str) -> None:
        self.instPath2Module = InstanceModuleMap(yamlFile)
        self.portXmls = PortXmlReader(xmlDir)
        self.portSet = set[InstancePort]()
        self.leafModuleSet = set[str]()
        with open(leafListFile, "r", encoding="utf-8") as leafList:
            # each line in leafList is <leaf module name>_leaf.v
            for line in leafList:
                # example: foo_leaf.v[0:-7] = foo
                leafName = line.strip()[:-7]
                self.leafModuleSet.add(leafName)

    def xmlDocOf(self, id: HierInstPath | str) -> Optional[PortXmlParser]:
        if isinstance(id, HierInstPath):
            moduleName = self.instPath2Module[id]
            if moduleName == None:
                return None
            return self.portXmls[moduleName]
        else:  # id is str
            return self.portXmls[id]

    def __newInstancePort(
        self,
        instPath: HierInstPath,
        moduleName: str,
        portName: str,
        dir: PortDir,
        isLeaf: bool,
        connec: list[InstancePort],
    ):
        instancePort = InstancePort()
        instancePort.instPath = instPath
        instancePort.moduleName = moduleName
        instancePort.portName = portName
        instancePort.dir = dir
        instancePort.isLeaf = isLeaf
        instancePort.connec = connec
        self.portSet.add(instancePort)
        return instancePort

    def fillPortConnec(
        self,
        aInstPath: HierInstPath,
        moduleName: str,
        portName: str,
        dir: PortDir,
        isLeaf: bool,
    ) -> list[InstancePort]:
        if isLeaf:
            return []
        parser = self.xmlDocOf(moduleName)
        assert parser is not None
        # assumpt bia log port name is same with bundle name, not wire name
        # one bundle only have one wire and bundle name is same with wire name
        wireConnec = parser.findByWire(portName)
        assert wireConnec is not None
        res = list[InstancePort]()
        for inner in wireConnec.inners:
            innerAbsInstPath = inner.rInstPath.toAbs(aInstPath)
            assert dir == inner.dir
            if inner.moduleName in self.leafModuleSet:
                leafPort = self.__newInstancePort(
                    innerAbsInstPath,
                    inner.moduleName,
                    inner.portSignal,
                    inner.dir,
                    True,
                    [],
                )
                res.append(leafPort)
            else:
                connec = self.fillPortConnec(
                    innerAbsInstPath,
                    inner.moduleName,
                    inner.portSignal,
                    inner.dir,
                    False,
                )
                blockPort = self.__newInstancePort(
                    innerAbsInstPath,
                    inner.moduleName,
                    inner.portSignal,
                    inner.dir,
                    False,
                    connec,
                )
                res.append(blockPort)
        return res

    def addInstancePort(
        self, absInstPathStr: str, portName: str, dir: PortDir
    ) -> Optional[InstancePort]:
        aInstPath: HierInstPath = HierInstPath(absInstPathStr, True)
        moduleName = self.instPath2Module[aInstPath]
        if moduleName == None:
            return None
        isLeaf: bool = moduleName in self.leafModuleSet
        connec: list[InstancePort] = self.fillPortConnec(
            aInstPath, moduleName, portName, dir, isLeaf
        )
        instancePort = self.__newInstancePort(
            aInstPath, moduleName, portName, dir, isLeaf, connec
        )
        return instancePort
