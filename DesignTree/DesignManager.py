from DesignTree.Utils import PortDir, HierInstPath
from DesignTree.InstancePort import *
from DesignTree.PortXml import *
import sys


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
                    inner.dir,
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
                #  branch module have sub instance
                branchPort = self.__newInstancePort(
                    innerAbsInstPath,
                    inner.moduleName,
                    inner.portWireName,
                    inner.dir,
                    False,
                    connec,
                )
                res.append(branchPort)
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
        # TODO: change assert to if
        if bundleConnec == None:
            portWire = self.__newInstancePort(
                aInstPath, moduleName, bundleName, bundleDir, True, []
            )
            print(
                f"Warn: miss bundle {bundleName} in {parentPath}_port.xml",
                file=sys.stderr,
            )
            return [portWire]
        for wireConnec in bundleConnec.wireList:
            for endBlock in wireConnec.inners:
                if endBlock.rInstPath.toAbs(parentPath) == aInstPath:
                    assert endBlock.wireLink is not None
                    assert endBlock.wireLink.bundleLink is not None
                    # TODO: assert, set bundleConnec.dir as many dir
                    # assert endBlock.wireLink.bundleLink.dir == bundleDir
                    assert endBlock.moduleName == moduleName
                    instPort = self.__newInstancePort(
                        aInstPath,
                        moduleName,
                        endBlock.portWireName,
                        endBlock.dir,
                        True,
                        [],
                    )
                    instPortList.append(instPort)
        return instPortList

    def __fromBranchBlockBundle(
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
        # TODO: assert, set bundleConnec.dir as many dir
        # assert bundleConnec.dir == bundleDir

        for wireConnec in bundleConnec.wireList:
            portWireName = wireConnec.outer.portWireName
            wireDir = wireConnec.outer.dir
            assert moduleName == wireConnec.outer.moduleName
            assert wireConnec.bundleLink is not None
            # TODO: assert, set bundleConnec.dir as many dir
            # assert bundleDir == wireConnec.bundleLink.dir

            connec: list[InstancePort] = self.recursivePortWire(absInstPath, wireConnec)
            if connec.__len__() == 0:
                print(
                    f"{absInstPath}_port.xml's wire {wireConnec.name} is not connected",
                    file=sys.stderr,
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
            return self.__fromBranchBlockBundle(
                aInstPath, moduleName, bundleName, bundleDir
            )
