from DesignTree.Utils import PortDir, HierInstPath
from DesignTree.InstancePort import *
from DesignTree.PortXml import *


class DesignManager:

    def __init__(self, yamlFile: str, xmlDir: str) -> None:
        self.instPath2Module = InstanceModuleMap(yamlFile)
        self.portXmls = PortXmlReader(xmlDir)
        self.portSet = set[InstancePort]()

    def isLeaf(self, moduleName: str):
        return self.instPath2Module.isLeaf(moduleName)

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
        range: tuple[int, int],
        isLeaf: bool,
        connec: list[InstancePort],
    ):
        instancePort = InstancePort()
        instancePort.instPath = instPath
        instancePort.moduleName = moduleName
        instancePort.portWireName = portName
        instancePort.wireDir = dir
        instancePort.range = range
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
            innerAbsInstPath = aInstPath + inner.instPath
            innerIsLeaf = self.isLeaf(inner.moduleName)
            assert innerIsLeaf is not None
            if innerIsLeaf:
                # port of leaf module
                leafPort = self.__newInstancePort(
                    innerAbsInstPath,
                    inner.moduleName,
                    inner.portWireName,
                    inner.wireDir,
                    wireConnec.range,
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
                    innerWireConnec.range,
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
                aInstPath, moduleName, bundleName, bundleDir, (0, 0), True, []
            )
            return [portWire]
        for wireConnec in bundleConnec.wireList:
            for endBlock in wireConnec.inners:
                if parentPath + endBlock.instPath == aInstPath:
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
                        wireConnec.range,
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
                wireConnec.range,
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
        isLeaf = self.isLeaf(moduleName)
        assert isLeaf is not None
        if isLeaf:
            return self.__fromLeafBlockBundle(
                aInstPath, moduleName, bundleName, bundleDir
            )
        else:
            return self.__fromContainerBundle(
                aInstPath, moduleName, bundleName, bundleDir
            )
