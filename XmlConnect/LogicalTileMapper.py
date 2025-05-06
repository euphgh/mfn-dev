from DesignTree import LogicalTopoGraph, TileTopoGraph, LogicalTileMap
import sys


def main():
    lgclDir: str = sys.argv[1]
    tileDir: str = sys.argv[2]
    topName: str = sys.argv[3]
    # create logical view
    lgclView = LogicalTopoGraph(f"{lgclDir}/logical_info.yml")
    success = lgclView.tops({topName})
    assert success == {topName}
    # create tile view
    tileView = TileTopoGraph(f"{tileDir}/tile_info.yml")
    tileView.tops({topName})
    assert success == {topName}

    LogicalTileMap(f"{tileDir}/logical2tile_hierarchy.map", topName, lgclView, tileView)

    # lgclView.createPortTopo(lgclDir)
    # tileView.createPortTopo(tileDir)


if __name__ == "__main__":
    main()
