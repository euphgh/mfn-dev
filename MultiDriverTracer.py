import sys
from DesignTree import *
from typing import Optional
import re
from io import StringIO


class InputParser:
    portPattern = r"\"(\w+):(\w+):(receive|transmit)\""
    instPattern = r"blkclass:(\w+) hier:(\w+)"

    def __init__(self, fileName: str) -> None:
        self.file = open(fileName, "r", encoding="utf-8")
        self.hier = str()
        self.blkClass = str()
        self.items: list[tuple[str, str, str]] = []

    def getContainer(self) -> str:
        if self.blkClass != self.hier:
            print(f"found blkClass: {self.blkClass} != hier:{self.hier}")
        return self.blkClass

    def nextItem(self) -> Optional[tuple[str, str, str]]:
        if self.items.__len__() == 0:
            return None
        item = self.items[0]
        self.items.pop(0)
        return item

    def readLine(self) -> bool:
        line = self.file.readline()
        if not line:
            self.file.close()
            return False

        # parser "blkClass:foo hier:bar.foo"
        match = re.search(InputParser.instPattern, line)
        assert match is not None
        self.blkClass = match.group(1)
        self.hier = match.group(2)

        # parser "zsc:ZSC_USB_CG_ctrl:transmit"
        matches = re.findall(InputParser.portPattern, line)
        for match in matches:
            instName = match[0]
            portName = match[1]
            dir = match[2]
            assert isinstance(instName, str)
            assert isinstance(portName, str)
            assert isinstance(dir, str)
            self.items.append((instName, portName, dir))
        return True


def format(instPath: HierInstPath, portName: str) -> str:
    instPathStr = instPath.join("/")
    return f"{instPathStr}/{portName}\n"


def printLeafPortOf(instPort: InstancePort):
    for leafPort in instPort.leaves():
        leafInstPath = leafPort.instPath
        if leafPort.range[0] - leafPort.range[1] == 0:
            outputs.write(format(leafInstPath, leafPort.portWireName))
        else:
            for i in range(leafPort.range[1], leafPort.range[0]):
                outputs.write(format(leafInstPath, f"{leafPort.portWireName}[{i}]"))


if __name__ == "__main__":
    multidriveLog: str = sys.argv[1]
    xmlDir: str = sys.argv[2]
    yamlFile: str = f"{xmlDir}/logical_info.yml"
    inputParser = InputParser(multidriveLog)
    designTree = DesignManager(yamlFile, xmlDir)
    outputs = open("outputs.txt", "w")
    while inputParser.readLine():
        container = inputParser.getContainer()
        while 1:
            result = inputParser.nextItem()
            if result is None:
                break
            instName, bundleName, bundleDir = result
            instPortList = None
            if container != instName:
                instPortList = designTree.addInstancePortFromBundle(
                    HierInstPath(container, instName),
                    bundleName,
                    PortDir.fromStr(bundleDir),
                )
            else:
                instPortList = designTree.addInstancePortFromBundle(
                    HierInstPath(container), bundleName, PortDir.fromStr(bundleDir)
                )
            for instPort in instPortList:
                printLeafPortOf(instPort)

    outputs.close()
