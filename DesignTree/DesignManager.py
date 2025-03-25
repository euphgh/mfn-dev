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
        instancePort.portWireName = portName
        instancePort.wireDir = dir
        instancePort.isLeaf = isLeaf
        instancePort.connec = connec
        if isLeaf:
            assert connec.__len__() == 0
        self.portSet.add(instancePort)
        return instancePort

    def recursivePortWire(
        self,
        aInstPath: HierInstPath,
        wireConnec: WireConnec,
    ) -> list[InstancePort]:
        res = list[InstancePort]()
        for inner in wireConnec.inners:
            innerAbsInstPath = inner.rInstPath.toAbs(aInstPath)
            if inner.moduleName in self.leafModuleSet:
                # port of leaf module
                leafPort = self.__newInstancePort(
                    innerAbsInstPath,
                    inner.moduleName,
                    inner.portWireName,
                    inner.wireDir,
                    True,
                    [],
                )
                res.append(leafPort)
            else:
                innerParser = self.xmlDocOf(innerAbsInstPath)
                assert innerParser
                innerWireConnec = innerParser.findByWire(inner.portWireName)
                assert innerWireConnec is not None
                connec = self.recursivePortWire(
                    innerAbsInstPath,
                    innerWireConnec,
                )
                # In contrast to the leaf module
                containerPort = self.__newInstancePort(
                    innerAbsInstPath,
                    inner.moduleName,
                    inner.portWireName,
                    inner.wireDir,
                    False,
                    connec,
                )
                res.append(containerPort)
        return res

    # leafBundle, the bundle connect leaf block
    def __fromLeafBlockBundle(
        self,
        aInstPath: HierInstPath,
        moduleName: str,
        bundleName: str,
        bundleDir: PortDir,
    ):
        instPortList = list[InstancePort]()
        parentPath = aInstPath.parent()
        parentParser = self.xmlDocOf(parentPath)
        assert parentParser is not None
        bundleConnec = parentParser.findByBundle(bundleName)
        if bundleConnec == None:
            cl.warning(f"miss bundle {bundleName} in {parentPath}_port.xml")
            portWire = self.__newInstancePort(
                aInstPath, moduleName, bundleName, bundleDir, True, []
            )
            return [portWire]
        for wireConnec in bundleConnec.wireList:
            for endBlock in wireConnec.inners:
                if endBlock.rInstPath.toAbs(parentPath) == aInstPath:
                    cl.warn_if(
                        endBlock.bundleDir != bundleDir,
                        f"port xml end_block {endBlock.portWireName}'s port_dir {endBlock.bundleDir} is diff with expected {bundleDir}",
                    )
                    assert endBlock.moduleName == moduleName
                    instPort = self.__newInstancePort(
                        aInstPath,
                        moduleName,
                        endBlock.portWireName,
                        endBlock.wireDir,
                        True,
                        [],
                    )
                    instPortList.append(instPort)
        cl.warn_if(
            instPortList.__len__() == 0,
            f"miss end_block {moduleName}:{bundleName} in {parentPath}_port.xml ",
        )
        return instPortList

    def __fromContainerBundle(
        self,
        absInstPath: HierInstPath,
        moduleName: str,
        bundleName: str,
        bundleDir: PortDir,
    ) -> list[InstancePort]:
        instPortList = list[InstancePort]()
        parser = self.xmlDocOf(moduleName)
        assert parser is not None

        bundleConnec = parser.findByBundle(bundleName)
        assert bundleConnec is not None
        cl.warn_if(
            bundleConnec.dir != bundleDir,
            f"port xml bundle's dir {bundleConnec.dir} is diff with expected {bundleDir}",
        )

        for wireConnec in bundleConnec.wireList:
            portWireName = wireConnec.outer.portWireName
            wireDir = wireConnec.outer.wireDir
            assert moduleName == wireConnec.outer.moduleName
            assert wireConnec.bundleLink is not None

            connec: list[InstancePort] = self.recursivePortWire(absInstPath, wireConnec)
            cl.warn_if(
                connec.__len__() == 0,
                f"{absInstPath}_port.xml's wire {wireConnec.name} is not connected",
            )
            outerInstPort = self.__newInstancePort(
                absInstPath,
                moduleName,
                portWireName,
                wireDir,
                False,
                connec,
            )
            instPortList.append(outerInstPort)
        return instPortList

    def addInstancePortFromBundle(
        self, absInstPathStr: str, bundleName: str, bundleDir: PortDir
    ) -> list[InstancePort]:
        aInstPath: HierInstPath = HierInstPath(absInstPathStr, True)
        moduleName = self.instPath2Module[aInstPath]
        assert moduleName is not None, f"not found instPath: {aInstPath}"
        isLeaf: bool = moduleName in self.leafModuleSet
        if isLeaf:
            return self.__fromLeafBlockBundle(
                aInstPath, moduleName, bundleName, bundleDir
            )
        else:
            return self.__fromContainerBundle(
                aInstPath, moduleName, bundleName, bundleDir
            )
