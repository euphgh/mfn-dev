from DesignTree.DesignTopoGraph import DesignTopoGraph, InstParentPath, ModuleNode
from DesignTree.Utils import *
import yaml
from pdb import set_trace


class LogicalTopoGraph(DesignTopoGraph):
    """
    Logical view deign topo graph
    """

    def __init__(self, yamlFile: str) -> None:
        super().__init__()
        with open(yamlFile, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            assert isinstance(data["CONTAINER_CLASS_NAMES"], list)
            containerNameList: list[str] = data["CONTAINER_CLASS_NAMES"]
            containerNameList = [x.strip() for x in containerNameList]
            # NOTE: logical view instParentPaths的最底层是leaf block
            assert isinstance(data["ALL_BLOCK_INSTANCE_PARENT_PATH"], list)
            strList: list[str] = data["ALL_BLOCK_INSTANCE_PARENT_PATH"]
            instParentPaths = [InstParentPath.fromStr(x) for x in strList]

            self.createModuleHier(containerNameList, instParentPaths)


class TileTopoGraph(DesignTopoGraph):
    """
    Tile view deign topo graph
    """

    def __init__(self, yamlFile: str) -> None:
        super().__init__()
        containerNameList = list[str]()
        instParentPaths = list[InstParentPath]()
        # containerSubInstList = list[str]()
        with open(yamlFile, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            assert isinstance(data["ALL_AUTOGEN_BLOCK_CLASS_NAMES"], list)
            containerNameList: list[str] = data["ALL_AUTOGEN_BLOCK_CLASS_NAMES"]
            containerNameList = [x.strip() for x in containerNameList]
            # NOTE: tile view instParentPaths的最底层是tile, 不是leaf block
            assert isinstance(data["ALL_AUTOGEN_BLOCK_INSTANCE_PARENT_PATH"], list)
            strList: list[str] = data["ALL_AUTOGEN_BLOCK_INSTANCE_PARENT_PATH"]
            instParentPaths = [InstParentPath.fromStr(x) for x in strList]

            # assert isinstance(data["TILE_CLASS_SUBBLOCK_NAMES"], list)
            # assert isinstance(data["CTNR_CLASS_SUBBLOCK_NAMES"], list)
            # containerSubInstList.extend(data["TILE_CLASS_SUBBLOCK_NAMES"])
            # containerSubInstList.extend(data["CTNR_CLASS_SUBBLOCK_NAMES"])

        self.createModuleHier(containerNameList, instParentPaths)
        # for subInstStr in containerSubInstList:
        #     container, subInst = subInstStr.strip().split(".")
        #     dictAdd(self.nodes[container].next, subInst, ModuleNode("__unknow__"))


def commonSplit(lhs: HierInstPath, rhs: HierInstPath):
    """
    get the common parent of lhs and rhs
    calcute the lhs and rhs part without common parent
    """
    common: HierInstPath
    lhsSub: HierInstPath
    rhsSub: HierInstPath
    if lhs.module != rhs.module:
        common = HierInstPath.empty()
        lhsSub = lhs
        rhsSub = rhs
    thisInstance = lhs.instances
    thatInstance = rhs.instances
    commonInstances = list[str]()
    idx: int = 0
    commonInstanceNum = min(thisInstance.__len__(), thatInstance.__len__())
    while idx < commonInstanceNum and thisInstance[idx] == thatInstance[idx]:
        idx = idx + 1

    common = HierInstPath(lhs.module, tuple(commonInstances))
    lhsSub = HierInstPath.empty()
    rhsSub = HierInstPath.empty()
    raise NotImplemented
    return (
        common,
        lhsSub,
        rhsSub,
    )


# immutable
@dataclass(frozen=True)
class MapLine:
    # logical inst path after common path
    lgcl: HierInstPath
    # tile inst path after common path
    tile: HierInstPath

    def lgclAbsInstPath(self) -> HierInstPath:
        return self.lgcl

    def tileAbsInstPath(self) -> HierInstPath:
        return self.tile


@dataclass(frozen=True)
class ModulesKey:
    # logical module name
    lgcl: str
    # tile module name
    tile: str


class LogicalTileMap:
    @staticmethod
    def pathStr2HierInstPath(path: str, topName: str):
        absInstPaths = path.split(".")
        for index in range(absInstPaths.__len__()):
            if absInstPaths[index] == topName:
                return HierInstPath(topName, tuple(absInstPaths[index + 1 :]))
        assert False

    # 读入mapFile
    def __init__(
        self,
        mapFile: str,
        prefix: str,
        lgclView: LogicalTopoGraph,
        tileView: TileTopoGraph,
    ) -> None:
        mapLines = list[MapLine]()
        self.lgclView = lgclView
        self.tileView = tileView
        with open(mapFile, "r", encoding="utf-8") as file:
            while 1:
                line = file.readline()
                if line == "":
                    break
                lgclPathStr, _, tilePathStr = line.split(" ")
                if (prefix not in lgclPathStr) or (prefix not in tilePathStr):
                    continue
                lgclPath = LogicalTileMap.pathStr2HierInstPath(lgclPathStr, prefix)
                tilePath = LogicalTileMap.pathStr2HierInstPath(tilePathStr, prefix)
                mapLine = MapLine(lgclPath, tilePath)
                mapLines.append(mapLine)
        # (logical module name, tile module name) -> list[inst path map line]
        self.moduleMap = dict[ModulesKey, set[MapLine]]()
        self.__processMapLine(mapLines)
        self.__checkMapLine()

    def __processMapLine(self, mapLines: list[MapLine]):
        for mapLine in mapLines:
            lgclModuleName = self.lgclView.moduleName(mapLine.lgclAbsInstPath())
            assert lgclModuleName is not None
            tileModuleName = self.tileView.moduleName(mapLine.tileAbsInstPath())
            assert tileModuleName is not None
            # if tileModuleName == None:  # tileModule is a leaf block
            #     tileAbsInstPath = mapLine.tileAbsInstPath()
            #     pModuleNodeInTile = self.tileView.moduleNode(tileAbsInstPath.parent())
            #     assert pModuleNodeInTile is not None
            #     leafModuleNodeInTile = pModuleNodeInTile.next[tileAbsInstPath.leaf()]
            #     assert leafModuleNodeInTile.name == "__unknown__"
            #     assert leafModuleNodeInTile.next.__len__() == 0
            #     leafModuleNodeInTile.name = lgclModuleName
            # else:
            key = ModulesKey(lgclModuleName, tileModuleName)
            mapLineSet = self.moduleMap.setdefault(key, set[MapLine]())
            mapLineSet.add(mapLine)

    def __checkMapLine(self):
        lgclModuleSet = self.lgclView.containers()
        tileModuleSet = self.tileView.containers()
        assert lgclModuleSet == {x.lgcl for x in self.moduleMap.keys()}
        assert tileModuleSet == {x.tile for x in self.moduleMap.keys()}
        for moduleKey, mapLines in self.moduleMap.items():
            lgclOuterSet = set(self.lgclView.outer(HierInstPath(moduleKey.lgcl, ())))
            lgclMapLineSet = {x.lgcl for x in mapLines}
            assert lgclOuterSet == lgclMapLineSet
            tileOuterSet = set(self.tileView.outer(HierInstPath(moduleKey.tile, ())))
            tileMapLineSet = {x.tile for x in mapLines}
            assert tileOuterSet == tileMapLineSet
