from DesignTree.Utils import PortDir, HierInstPath
from DesignTree.InstancePort import *
from DesignTree.PortXml import *


class DesignManager:

    def __init__(self, yamlFile: str, xmlDir: str) -> None:
        self.hierTree = HierTree(yamlFile)
        self.portXmls = PortXmlReader(xmlDir, self.hierTree.containers())
        self.portSet = set[InstancePort]()

    # get module name of for the HierInstPath
    def moduleName(self, instPath: HierInstPath):
        return self.hierTree.moduleName(instPath)

    def isLeaf(self, id: str | HierInstPath):
        if isinstance(id, str):
            return self.hierTree.isLeaf(id)
        else:
            module = self.moduleName(id)
            if module:
                return self.hierTree.isLeaf(module)
            else:
                return False

    def xmlDocOf(self, id: HierInstPath | str) -> Optional[PortXmlParser]:
        if isinstance(id, HierInstPath):
            moduleName = self.moduleName(id)
            if moduleName == None:
                return None
            return self.portXmls[moduleName]
        else:  # id is str
            return self.portXmls[id]

    def concate(
        self, left: HierInstPath, right: HierInstPath
    ) -> Optional[HierInstPath]:
        if self.moduleName(left) == right.module:
            return HierInstPath(left.module, left.instances + right.instances)
        else:
            return None

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

    def __recursivePortWire(
        self,
        instPath: HierInstPath,
        wireConnec: WireConnec,
    ) -> list[InstancePort]:
        res = list[InstancePort]()
        for inner in wireConnec.inners:
            innerInstPath = instPath.addInst(inner.instName)
            innerIsLeaf = self.isLeaf(inner.moduleName)
            assert innerIsLeaf is not None
            if innerIsLeaf:
                # port of leaf module
                leafPort = self.__newInstancePort(
                    innerInstPath,
                    inner.moduleName,
                    inner.portWireName,
                    inner.wireDir,
                    wireConnec.range,
                    True,
                    [],
                )
                res.append(leafPort)
            else:
                innerParser = self.xmlDocOf(innerInstPath)
                assert innerParser
                innerWireConnec = innerParser.findByWire(inner.portWireName)
                assert innerWireConnec is not None
                connec = self.__recursivePortWire(
                    innerInstPath,
                    innerWireConnec,
                )
                # In contrast to the leaf module
                containerPort = self.__newInstancePort(
                    innerInstPath,
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
                if parentPath.addInst(endBlock.instName) == aInstPath:
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
        instPath: HierInstPath,
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

            connec: list[InstancePort] = self.__recursivePortWire(instPath, wireConnec)
            cl.warn_if(
                connec.__len__() == 0,
                f"{instPath}_port.xml's wire {wireConnec.name} is not connected",
            )
            outerInstPort = self.__newInstancePort(
                instPath,
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
        self, instPath: HierInstPath, bundleName: str, bundleDir: PortDir
    ) -> list[InstancePort]:
        moduleName = self.moduleName(instPath)
        assert moduleName is not None, f"not found instPath: {instPath}"
        isLeaf = self.isLeaf(moduleName)
        assert isLeaf is not None
        if isLeaf:
            return self.__fromLeafBlockBundle(
                instPath, moduleName, bundleName, bundleDir
            )
        else:
            return self.__fromContainerBundle(
                instPath, moduleName, bundleName, bundleDir
            )
