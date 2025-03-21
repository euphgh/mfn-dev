import sys
from DesignTree import *

class InputParser:
    pattern = r"\"(\w+):(\w+):(receive|transmit)\""
    def __init__(self, fileName:str) -> None:
        pass

    def getHier(self)->str:
        return ""

    def nextItem(self)->tuple[bool, tuple[str, str, str]]:
        return (False, ("", "", ""))

    def readLine(self)->bool:
        return True

if __name__ == "__main__":
    multidriveLog:str = sys.argv[1]
    inputParser = InputParser(multidriveLog)
    while inputParser.readLine():
        hierPrefix = HierInstPath(inputParser.getHier())
        portSet: set[InstancePort] = set()
        while 1:
            valid, result = inputParser.nextItem()
            if valid == False: break
            instanceName, portName, dirStr = result
        