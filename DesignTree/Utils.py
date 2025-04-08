"""
utils and basic class used in DesignTree

variable
cl: for logging information about DesignTree

class
HierInstPath: present module and instances hierarchy
PortDir: present the direct of wire or bundle
"""

from enum import Enum
import logging
from typing import Dict, Set, TypeVar
from dataclasses import dataclass

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
fileHandler = logging.FileHandler("DesignTree.log", "w")
fileHandler.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(levelname)s: %(message)s")
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


@dataclass(frozen=True)
class HierInstPath:
    """
    representing module and instances hierarchy
    note: this class is immutable, like tuple and str in python

    self.module: the module name of the start of this path
    self.instances: instance name path under this module
    If you want to add or sub the HierInstPath, it need the module and instance path information.
    please use DesignManager.add/sub to process two HierInstPath.
    """

    module: str
    instances: tuple[str, ...]

    @staticmethod
    def fromStr(moduleName: str, path: str) -> "HierInstPath":
        return HierInstPath(moduleName, tuple(path.split(".")))

    def join(self, split: str) -> str:
        return split.join((self.module,) + self.instances)

    def parent(self) -> "HierInstPath":
        assert self.instances.__len__() > 0
        return HierInstPath(self.module, self.instances[:-1])

    def leaf(self) -> str:
        return self.instances[-1]

    def addInst(self, that: str):
        return HierInstPath(self.module, self.instances + (that,))

    def common(self, that: "HierInstPath"):
        if self.module != that.module:
            return HierInstPath.empty()
        thisInstance = self.instances
        thatInstance = self.instances
        commonInstances = list[str]()
        for idx in range(min(thisInstance.__len__(), thatInstance.__len__())):
            if thisInstance[idx] == thatInstance[idx]:
                commonInstances.append(thisInstance[idx])
        return HierInstPath(self.module, tuple(commonInstances))

    @staticmethod
    def empty() -> "HierInstPath":
        return HierInstPath("", ())


class PortDir(Enum):
    """
    enum class to present the direct
    """

    EMPTY = 0  # only for init
    INPUT = 1  # input or receive
    OUTPUT = 2  # output or transmit
    INOUT = 3  # inout or bidirect

    @staticmethod
    def fromStr(dir: str) -> "PortDir":
        """
        Parser direct string to PortDir
        """
        inputSet = {"receive", "input", "transmit_in"}
        outputSet = {"transmit", "output", "transmit_out"}
        ioSet = {"bidirect", "inout"}
        if dir in inputSet:
            return PortDir.INPUT
        if dir in outputSet:
            return PortDir.OUTPUT
        if dir in ioSet:
            return PortDir.INOUT
        assert False, f"Direct str {dir} is not expected"


@dataclass(frozen=True)
class WireRange:
    msb: int
    lsb: int

K = TypeVar("K")  # 泛型键类型
V = TypeVar("V")  # 泛型值类型


def dictAdd(d: Dict[K, V], key: K, value: V, error: bool = True):
    assert key not in d, f"dict add duplicate for key {key}"
    d[key] = value
    return True


def setAdd(s: Set[K], key: K, error: bool = True):
    assert key not in s, f"set add duplicate for key {key}"
    s.add(key)
    return True
