from .DesignTopoGraph import DesignTopoGraph
from .DesignTopoGraph import InstParentPath, ModuleNode, ModuleLink
from .Utils import HierInstPath, compareSet, cl
from dataclasses import dataclass
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
        blockClassNameList = list[str]()
        instParentPaths = list[InstParentPath]()
        with open(yamlFile, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            assert isinstance(data["ALL_AUTOGEN_BLOCK_CLASS_NAMES"], list)
            blockClassNameList: list[str] = data["ALL_AUTOGEN_BLOCK_CLASS_NAMES"]
            blockClassNameList = [x.strip() for x in blockClassNameList]
            # NOTE: tile view instParentPaths的最底层是tile, 不是leaf block
            assert isinstance(data["ALL_AUTOGEN_BLOCK_INSTANCE_PARENT_PATH"], list)
            strList: list[str] = data["ALL_AUTOGEN_BLOCK_INSTANCE_PARENT_PATH"]
            instParentPaths = [InstParentPath.fromStr(x) for x in strList]

            assert isinstance(data["TILE_CLASS_SUBBLOCK_NAMES"], list)
            assert isinstance(data["CTNR_CLASS_SUBBLOCK_NAMES"], list)

        self.createModuleHier(blockClassNameList, instParentPaths)

        # container class sub block info is included in all auto gen block instance parent path
        for subInstStr in data["CTNR_CLASS_SUBBLOCK_NAMES"]:
            container, subInst = subInstStr.strip().split(".")
            assert container in self.nodes
            assert subInst in self.nodes[container].next

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
    raise NotImplementedError
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
                lgclPathStr, _, tilePathStr = line.strip().split(" ")
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
            if lgclModuleName is None:
                cl.warning(f"logical inst path {mapLine.lgcl} in map line is not exist")
                continue
            tileModuleName = self.tileView.moduleName(mapLine.tileAbsInstPath())
            if tileModuleName is None:  # tileModule is a leaf block
                tileAbsInstPath = mapLine.tileAbsInstPath()
                pModuleNodeInTile = self.tileView.moduleNode(tileAbsInstPath.parent())
                leafInstName = tileAbsInstPath.leaf()
                assert pModuleNodeInTile is not None
                # create new leaf module node
                leafModuleNodeInTile = self.tileView.nodes.setdefault(
                    lgclModuleName, ModuleNode(lgclModuleName)
                )
                # link module
                pModuleNodeInTile.next[leafInstName] = leafModuleNodeInTile
                moduleLink = ModuleLink(pModuleNodeInTile.name, leafInstName)
                leafModuleNodeInTile.prev[moduleLink] = pModuleNodeInTile
                # assign tile module name for later map
                tileModuleName = lgclModuleName
            if tileModuleName == lgclModuleName:
                key = ModulesKey(lgclModuleName, tileModuleName)
                mapLineSet = self.moduleMap.setdefault(key, set[MapLine]())
                mapLineSet.add(mapLine)
            else:
                cl.warning(f"skip mapLine {mapLine} for module name not same")

    def __checkMapLine(self):
        lgclModuleSet = self.lgclView.modules()
        tileModuleSet = self.tileView.modules()
        lgclModuleInMap = {x.lgcl for x in self.moduleMap.keys()}
        tileModuleInMap = {x.tile for x in self.moduleMap.keys()}
        assert lgclModuleInMap.issubset(lgclModuleSet)
        assert tileModuleInMap.issubset(tileModuleSet)

        for moduleKey, mapLines in self.moduleMap.items():
            lgclOuterSet = set(self.lgclView.outer(HierInstPath(moduleKey.lgcl, ())))
            lgclMapLineSet = {x.lgcl for x in mapLines}
            compareSet(lgclOuterSet, lgclMapLineSet)
            tileOuterSet = set(self.tileView.outer(HierInstPath(moduleKey.tile, ())))
            tileMapLineSet = {x.tile for x in mapLines}
            compareSet(tileOuterSet, tileMapLineSet)