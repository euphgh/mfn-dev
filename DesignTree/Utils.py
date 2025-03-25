from enum import Enum
import copy
import logging


class ErrorRaisingHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        raise RuntimeError(record.getMessage())


class CondLogger(logging.Logger):
    def warn_if(self, cond: bool, msg: str):
        if cond:
            self.warning(msg)

# 控制台
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.ERROR)

# 文件输出
fileHandler = logging.FileHandler("DesignTree.log")
fileHandler.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(levelname)s:%(message)s")
consoleHandler.setFormatter(formatter)
fileHandler.setFormatter(formatter)

errorHandler = ErrorRaisingHandler()
errorHandler.setLevel(logging.ERROR)

# 创建 Logger
logging.setLoggerClass(CondLogger)
logger = logging.getLogger("DesignTree")
# 添加 Handler
logger.setLevel(logging.DEBUG)
logger.addHandler(consoleHandler)
logger.addHandler(fileHandler)
logger.addHandler(errorHandler)

assert isinstance(logger, CondLogger)
cl: CondLogger = logger

# hierarchy instance name
# mutable
class HierInstPath:
    # fullName: foo.bar
    # if foo is top module name, the parentModuleName is "/", that is abs path
    # else foo is normal module name, the parentModuleName is "foo", is a relative path
    # abs: absolute path or relative path
    def __init__(self, fullName: str, isAbs: bool) -> None:
        self.nameList = fullName.split(".")
        self.isAbs = isAbs

    def __str__(self) -> str:
        if self.isAbs:
            return "/" + ".".join(self.nameList)
        else:
            return "." + ".".join(self.nameList)

    def join(self, split: str) -> str:
        return split.join(self.nameList)

    def append(self, tail: "str|HierInstPath") -> None:
        if isinstance(tail, str):
            self.nameList.append(tail)
        else:
            self.nameList.extend(tail.nameList)

    def parent(self) -> "HierInstPath":
        parentPath = copy.deepcopy(self)
        assert parentPath.nameList.__len__() > 1
        parentPath.nameList.pop()
        return parentPath

    def __eq__(self, value: object) -> bool:
        if isinstance(value, HierInstPath):
            return self.__str__() == value.__str__()
        return False

    def __add__(self, that: "HierInstPath"):
        assert self.isAbs or not that.isAbs
        res = copy.deepcopy(self)
        res.append(that)
        return res

    def __hash__(self) -> int:
        return hash(self.__str__())

    @staticmethod
    def empty() -> "HierInstPath":
        return HierInstPath("", False)


class PortDir(Enum):

    EMPTY = 0
    INPUT = 1
    OUTPUT = 2
    INOUT = 3

    @staticmethod
    def fromStr(dir: str) -> "PortDir":
        if dir == "receive":
            return PortDir.INPUT
        if dir == "transmit":
            return PortDir.OUTPUT
        if dir == "output":
            return PortDir.OUTPUT
        if dir == "input":
            return PortDir.INPUT
        if dir == "inout":
            return PortDir.INOUT
        if dir == "bidirect":
            return PortDir.INOUT
        assert False, f"Direct str {dir} is not expected"
