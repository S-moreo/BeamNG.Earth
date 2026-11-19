import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import unittest
import numpy as np
import roads
import navgraph
import osmtags
import mapgeom
from test_roadlanes import highway
from test_roads import FRAME, flat, rules


class HighwayShouldersTest(unittest.TestCase):
    def test_dimensions_paint_and_bridges_use_same_travel_lanes(self):
        for direction in (1, -1):
            for link, lanes, lane_w, left, right in ((False, 3, 4., 1.5, 4.5), (True, 1, 4.8, .875, 2.625),
                                                     (True, 2, 4.8, .875, 2.625)):
                f = highway(link=link, direction=direction)
                osmtags.join(f, {1: {'lanes': lanes}})
                sp = roads.road_specs(f)[0]
                self.assertAlmostEqual(sp.width, lane_w*lanes+left+right)
                self.assertAlmostEqual(roads.lane_layout(sp)[0], lane_w*lanes)
                self.assertEqual(roads.lane_layout(sp)[1], lanes)
                self.assertAlmostEqual(roads.edge_margin(sp, direction), left)
                self.assertAlmostEqual(roads.edge_margin(sp, -direction), right)
                pts = np.array([[0.,0.,0.],[200.,0.,0.]])
                for osm in (None, {'lanes':str(lanes)}):
                    paint = roads.extras(sp, pts, -85., country='US', osm=osm)
                    edges = {look['side']: float(p[0,1]) for look,w,p in paint if look.get('kind')=='edge'}
                    self.assertAlmostEqual(edges[1]-edges[-1], lane_w*lanes)
                    centre = sum(edges.values())/2
                    dividers = {round(float(p[0,1]),4) for look,w,p in paint if look.get('kind')=='lane'}
                    self.assertEqual(dividers, {round(centre-lane_w*lanes/2+k*lane_w,4) for k in range(1,lanes)})
                f.rules['flags'] = rules([(0,'is_bridge',0.,1.)])
                f = mapgeom.Features.from_arrays('roads', f.to_arrays(''), '')
                bridge = roads.bridge_specs(f)[0]
                self.assertEqual((bridge.width,bridge.lanes), (sp.width,sp.lanes))
                self.assertEqual(roads.lane_layout(bridge), roads.lane_layout(sp))

    def test_urban_freeways_keep_shoulders_and_ai_follows_paint(self):
        for direction in (1, -1):
            f=highway(direction=direction)
            osmtags.join(f,{1:{'lanes':3}})
            sp=roads.road_specs(f,lambda la,lo: np.ones_like(la,bool))[0]
            self.assertEqual(sp.width,18.)
            self.assertEqual(roads.lane_layout(sp),(12.,3))
            graph=navgraph.build(FRAME,[f],flat,(0.,0.))
            self.assertTrue(graph['nodes'])
            for node in graph['nodes'].values():
                self.assertAlmostEqual(node[1], direction*1.5, places=3)
            self.assertEqual({(e[3],e[4]) for e in graph['edges']},{(3,0)})

    def test_shifted_ai_stays_at_bridge_height(self):
        for direction in (1, -1):
            f = highway(direction=direction, flags=[(0, 'is_bridge')])
            osmtags.join(f, {1: {'lanes': 3}})
            decks = {str(f.ids[0]): [(np.array([[0.,0.],[100.,0.]]), np.array([20.,20.]), 2.)]}
            graph = navgraph.build(FRAME, [f], flat, (0.,0.), decks=decks)
            self.assertTrue(graph['nodes'])
            self.assertEqual({(e[3],e[4]) for e in graph['edges']}, {(3,0)})
            for node in graph['nodes'].values():
                self.assertAlmostEqual(node[1], direction*1.5, places=3)
                self.assertGreaterEqual(node[2], 20.)

    def test_lines_meet_a_deck_of_another_width(self):
        # a highway tapering into a deck of another width (road_tapers: its width at the joint the deck's) has the
        # deck's shoulders there, so its edge and lane lines go on into the deck's; from its own width a 12 m road
        # into a 14 m deck kept 2 m shoulders against the deck's 3 m: its edge lines stepped 1.5 m, its lane line 0.5 m
        pts = np.array([[0., 0., 0.], [50., 0., 0.], [100., 0., 0.]])
        for direction in (1, -1):
            for link, lanes, ground_w, deck_w in ((False, 2, 12., 14.), (False, 2, 14., 12.), (True, 1, 7.5, 9.)):
                cls = 'motorway'
                ground = roads.Spec(ground_w, 'paved', False, cls, True, dir=direction, lanes=lanes, link=link)
                deck = ground._replace(width=deck_w)

                def lines(sp, ws=None):
                    return sorted((look['kind'], look.get('side'), round(float(p[-1, 1]), 4))       # (at the joint)
                                  for look, w, p in roads.extras(sp, pts, -85., country='US', ws=ws)
                                  if look.get('kind') in ('edge', 'lane') and p[-1, 0] > 99.)
                self.assertEqual(lines(ground, np.array([ground_w, (ground_w + deck_w) / 2, deck_w])), lines(deck))
                self.assertEqual(lines(ground, np.full(3, ground_w)), lines(ground))     # (untapered: as before)

    def test_an_auxiliary_lane_taper_keeps_the_shoulders(self):
        # a 3-lane section (lanesections) narrowing to its 2-lane neighbour's 14 m at the joint: the edge lines meet
        # the neighbour's (its spec's shoulders); from the drawn width the white edge stepped 3 m (I-70, Washington PA)
        pts = np.array([[0., 0., 0.], [50., 0., 0.], [100., 0., 0.]])
        sec = roads.Spec(18., 'paved', False, 'motorway', True, dir=1, lanes=3)
        nb = sec._replace(width=14., lanes=2)

        def edges(sp, ws=None, aux=False):
            return sorted((look.get('side'), round(float(p[-1, 1]), 4))
                          for look, w, p in roads.extras(sp, pts, -80., country='US', ws=ws, aux=aux)
                          if look.get('kind') == 'edge' and p[-1, 0] > 99.)
        self.assertEqual(edges(sec, np.array([18., 16., 14.]), aux=True), edges(nb))


if __name__=='__main__':
    unittest.main()
