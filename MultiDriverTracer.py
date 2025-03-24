import sys
from DesignTree import *
from typing import Optional
import re


class InputParser:
    portPattern = r"\"(\w+):(\w+):(receive|transmit)\""
    instPattern = r"blkclass:(\w+) hier:(\w+)"

    def __init__(self, fileName: str) -> None:
        self.file = open(fileName, "r", encoding="utf-8")
        self.hier = str()
        self.blkClass = str()
        self.items: list[tuple[str, str, str]] = []

    def getHier(self) -> str:
        if self.blkClass != self.hier:
            print(f"found blkClass: {self.blkClass} != hier:{self.hier}")
        return self.hier

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


if __name__ == "__main__":
    multidriveLog: str = sys.argv[1]
    yamlFile: str = sys.argv[2]
    xmlDir: str = sys.argv[3]
    leaflistFile: str = sys.argv[4]
    inputParser = InputParser(multidriveLog)
    designTree = DesignManager(yamlFile, xmlDir, leaflistFile)
    while inputParser.readLine():
        hierPrefix = inputParser.getHier()
        portSet: set[InstancePort] = set()
        while 1:
            result = inputParser.nextItem()
            if result is None:
                break
            instanceName, portName, dirStr = result
            instancePort = designTree.addInstancePort(
                f"{hierPrefix}.{instanceName}", portName, PortDir.fromStr(dirStr)
            )
            assert instancePort is not None
            for leaf in instancePort.leaves():
                print(leaf)
            print()
