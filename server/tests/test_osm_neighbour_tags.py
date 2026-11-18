"""A road's OpenStreetMap tags from the cells its line crosses into (mapdata.MapData._osm_from_neighbours): I-70 by
Washington PA (2026-11-18), a ~600 m Overture segment naming a 250 m way wholly in the next cell east, had no OSM lanes
in the two cells west of it, so its copies guessed 1 and 3 lanes against the map's 2."""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mapcells  # noqa: E402
import mapdata  # noqa: E402
import mapgeom  # noqa: E402

WEST, EAST = mapcells.CellKey(14, 4538, 6192), mapcells.CellKey(14, 4539, 6191)


def road(record, pts):
    f = mapgeom.Features("roads", np.array(["seg"]), np.full(1, mapgeom.LINE, np.uint8), np.array([0, 1], np.int64),
                         np.array([0, 1], np.int64), np.array([0, len(pts)], np.int64), np.array(pts, np.float64))
    f.attrs["src_record"] = mapgeom.text_column([record])
    return f


class FakeMapData(mapdata.MapData):
    def __init__(self, cells):
        self.cells, self.asked = cells, []

    def _osm_cell(self, key, kind):
        self.asked.append(str(key))
        return self.cells.get(str(key), ({}, []))


class NeighbourTags(unittest.TestCase):
    LINE = [(-80.2671, 40.1782), (-80.2645, 40.1805), (-80.2616, 40.1829)]     # (from WEST into EAST)

    def test_way_held_by_the_next_cell_joins(self):
        md = FakeMapData({str(EAST): ({37728837: {"lanes": "2"}, 5: {"lanes": "4"}}, [])})
        tags, ways = md._osm_from_neighbours(WEST, "demand", road("w37728837@13", self.LINE), ({1: {}}, ["x"]))
        self.assertEqual(tags, {1: {}, 37728837: {"lanes": "2"}})      # (only the way it names)
        self.assertEqual(ways, ["x"])
        self.assertEqual(md.asked, [str(EAST)])

    def test_own_cells_tags_are_kept_and_nothing_asked(self):
        md = FakeMapData({str(EAST): ({37728837: {"lanes": "3"}}, [])})
        own = ({37728837: {"lanes": "2"}}, [])
        self.assertIs(md._osm_from_neighbours(WEST, "demand", road("w37728837@13", self.LINE), own), own)
        self.assertEqual(md.asked, [])

    def test_a_road_inside_its_cell_asks_no_neighbour(self):
        md = FakeMapData({})
        inside = [(-80.2671, 40.1782), (-80.2665, 40.1786)]
        md._osm_from_neighbours(WEST, "demand", road("w9@1", inside), ({}, []))
        self.assertEqual(md.asked, [])

    def test_no_way_id_no_lookup(self):
        md = FakeMapData({})
        md._osm_from_neighbours(WEST, "demand", road("r123@1", self.LINE), ({}, []))
        self.assertEqual(md.asked, [])


if __name__ == "__main__":
    unittest.main()
