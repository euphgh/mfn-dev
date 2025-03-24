from DesignTree.Utils import PortDir, HierInstPath
from typing import Optional
import yaml


class InstanceModuleMap:

    def __init__(self, yamlFile: str) -> None:
        self.instPath2Module: dict[HierInstPath, str] = {}
        # yaml file example: <instance path>:<module name>
        # ALL_BLOCK_INSTANCE_PARENT_PATH:
        #   - dchub.dchubbubl:dchubbubl_wrapper
        #   - dchub.dchubbubmem0:dchubbubmem_wrapper
        with open(yamlFile, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            assert isinstance(data, dict)
            assert "ALL_BLOCK_INSTANCE_PARENT_PATH" in data
            for pair in data["ALL_BLOCK_INSTANCE_PARENT_PATH"]:
                assert isinstance(pair, str)
                instPathStr, moduleName = pair.split(":")
                self.instPath2Module[HierInstPath(instPathStr, True)] = moduleName

    def __getitem__(self, instPath: HierInstPath) -> Optional[str]:
        return self.instPath2Module.get(instPath, None)

    def __str__(self) -> str:
        return self.instPath2Module.__str__()


class InstancePort:

    def __init__(self) -> None:
        self.instPath = HierInstPath.empty()
        self.moduleName = str()
        self.portName = str()
        self.dir = PortDir.EMPTY
        self.isLeaf = False
        self.connec = list["InstancePort"]()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, InstancePort):
            return self.instPath == other.instPath and self.portName == other.portName
        return False

    def __hash__(self):
        return hash(self.instPath.__str__() + self.portName)

    def leaves(self) -> list["InstancePort"]:
        if self.isLeaf:
            return [self]
        res: list["InstancePort"] = []
        for connec in self.connec:
            res.extend(connec.leaves())
        return res

    def __str__(self) -> str:
        if self.isLeaf:
            return f"leaf: {self.instPath.__str__()}:{self.portName}:{self.dir}"
        else:
            return f"branch: {self.instPath.__str__()}:{self.portName}:{self.dir}"
