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


class HierInstPath:
    """
    representing module and instances hierarchy
    note: this class is immutable, like tuple and str in python

    self.module: the module name of the start of this path
    self.instances: instance name path under this module
    If you want to add or sub the HierInstPath, it need the module and instance path information.
    please use DesignManager.add/sub to process two HierInstPath.
    """

    def __init__(self, module: str, instances: "str|tuple[str, ...]" = ()) -> None:
        self.module = module
        if isinstance(instances, str):
            self.instances = tuple(instances.split("."))
        else:
            self.instances = instances

    def __str__(self) -> str:
        return self.join(".")

    def join(self, split: str) -> str:
        return split.join((self.module,) + self.instances)

    def parent(self) -> "HierInstPath":
        assert self.instances.__len__() > 0
        return HierInstPath(self.module, self.instances[:-1])

    def addInst(self, that: str):
        return HierInstPath(self.module, self.instances + (that,))

    def __eq__(self, value: object) -> bool:
        if isinstance(value, HierInstPath):
            return self.__str__() == value.__str__()
        return False

    def __hash__(self) -> int:
        return hash(self.__str__())

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


class WireRange:

    def __init__(self, msb: int = 0, lsb: int = 0) -> None:
        self.msb: int = msb
        self.lsb: int = lsb
