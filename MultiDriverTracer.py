import sys
from DesignTree import *
from typing import Optional
import re
from pdb import set_trace


class InputParser:
    portPattern = r"\"(\w+):(\w+):(receive|transmit)\""
    containerPattern = r"blkclass:(\w+) hier:(\w+)"
    bundlePattern = r"ERROR:  inst:(\w+)\("

    def __init__(self, fileName: str) -> None:
        self.file = open(fileName, "r", encoding="utf-8")
        self.hier = str()
        self.container = str()
        self.bundle = str()
        self.items: list[tuple[str, str, str]] = []

    def getContainer(self) -> str:
        return self.container

    def getBundle(self) -> str:
        return self.bundle

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
        match = re.search(InputParser.containerPattern, line)
        assert match is not None
        self.container = match.group(1)

        # parser "inst:bundleName"
        match = re.search(InputParser.bundlePattern, line)
        assert match is not None
        self.bundle = match.group(1)

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


def printLeafPortOf(instPath: HierInstPath, portNdoe: PortWireNode, hierTree: HierTree):
    for absPath in hierTree.forward(instPath):
        if portNdoe.range.msb - portNdoe.range.lsb == 0:
            outputs.write(format(absPath, portNode.name))
        else:
            for i in range(portNode.range.lsb, portNode.range.msb + 1):
                outputs.write(format(absPath, f"{portNode.name}[{i}]"))


if __name__ == "__main__":
    multidriveLog: str = sys.argv[1]
    xmlDir: str = sys.argv[2]
    yamlFile: str = f"{xmlDir}/logical_info.yml"
    inputParser = InputParser(multidriveLog)
    outputs = open("outputs.txt", "w")
    print("start load yaml file")
    hierTree = HierTree(yamlFile)
    print("finish load yaml file")
    success = hierTree.tops({"mpu"})
    assert success == {"mpu"}
    print("start load xml file")
    hierTree.createPortTopo(xmlDir)
    print("finish load xml file")
    while inputParser.readLine():
        container = inputParser.getContainer()
        bundle = inputParser.getBundle()
        moduleNode = hierTree.nodes[container]
        assert moduleNode is not None
        portNodes = moduleNode.bundleOf(bundle)
        assert portNodes is not None

        set_trace()
        for portNode in portNodes:
            res = portNode.leaves(HierInstPath(container))
            for leafInstPath, leafNode in res:
                printLeafPortOf(leafInstPath, leafNode, hierTree)

    outputs.close()
