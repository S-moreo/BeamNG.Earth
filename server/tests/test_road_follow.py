"""BNE_ROAD_FOLLOW (roads keep the land's crests and dips): grading.profile_sigma with the switch on and off."""
import os
import sys
import unittest
from unittest import mock

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import grading  # noqa: E402
import roads  # noqa: E402


def spec(cls, urban=False, **kw):
    return roads.Spec(7.0, "paved", urban, cls, **kw)


class FollowTest(unittest.TestCase):
    def test_off_is_unchanged(self):
        with mock.patch.object(grading, "FOLLOW_ON", False):
            self.assertEqual(grading.profile_sigma(spec("tertiary")), 20.0)
            self.assertEqual(grading.profile_sigma(spec("primary")), grading.SIGMA_MAJOR_M)

    def test_on_shorter_for_minor_classes_majors_kept(self):
        with mock.patch.object(grading, "FOLLOW_ON", True):
            self.assertEqual(grading.profile_sigma(spec("tertiary")), 6.0)
            self.assertEqual(grading.profile_sigma(spec("primary")), 12.0)
            self.assertEqual(grading.profile_sigma(spec("tertiary", link=True)), grading.FOLLOW_LINK_SIGMA_M)
            self.assertEqual(grading.profile_sigma(spec("motorway")), grading.SIGMA_MAJOR_M)
            self.assertEqual(grading.profile_sigma(spec("trunk")), grading.SIGMA_MAJOR_M)
            self.assertEqual(grading.profile_sigma(roads.Spec(4.0, "gravel", False, "track")),
                             grading.DIRT_SIGMA_MINOR_M)      # dirt roads as before

    def test_median_shorter_below_trunk_roads_only(self):
        with mock.patch.object(grading, "FOLLOW_ON", False):
            self.assertEqual(grading.profile_median(spec("tertiary")), grading.MEDIAN_M)
        with mock.patch.object(grading, "FOLLOW_ON", True):
            self.assertEqual(grading.profile_median(spec("tertiary")), grading.FOLLOW_MEDIAN_M)
            self.assertEqual(grading.profile_median(spec("primary", link=True)), grading.FOLLOW_MEDIAN_M)
            # (motorways and trunks keep the long median that takes coarse elevation's tree and bridge spikes out, #271)
            self.assertEqual(grading.profile_median(spec("motorway")), grading.MEDIAN_M)
            self.assertEqual(grading.profile_median(spec("trunk")), grading.MEDIAN_M)
            self.assertEqual(grading.profile_median(roads.Spec(4.0, "gravel", False, "track")), grading.DIRT_MEDIAN_M)
        self.assertEqual(grading.MEDIAN_M, float(os.environ.get("BNE_GRADE_MEDIAN", "24")))   # (never changed in place)

    def test_on_keeps_a_100m_dip(self):
        s = np.arange(0.0, 600.0, grading.PROFILE_STEP)
        z = -2.0 * np.exp(-((s - 300.0) / 25.0) ** 2)         # a 2 m dip about 100 m across
        kept = {}
        for on in (False, True):
            with mock.patch.object(grading, "FOLLOW_ON", on):
                zs = grading.smooth_profile(z, grading.PROFILE_STEP, grading.profile_sigma(spec("tertiary")))
            kept[on] = -float(zs.min()) / 2.0
        self.assertLess(kept[False], 0.7)
        self.assertGreater(kept[True], 0.85)


class SquareFollowTest(unittest.TestCase):
    """The road system's profile squares (BNE_ROADSYS=heights and on): the switch where the ground is not coarse."""

    def setUp(self):
        import fast
        if not fast.AVAILABLE or int(getattr(fast._ef, "VERSION", 0)) < 623:
            self.skipTest("earthfast 623 (roadsys_square follow=) not built")
        self.fast = fast

    def dip_kept(self, cls, kmh, follow):
        """The depth a road in square (0, 0) keeps of a 100 m long, 2 m deep dip at the square's centre, on the approach
        to its bridge 70 m on (a square holds the roads round structures)."""
        from tests.test_roadsys import seg, table

        def ground(e, n):
            x = np.asarray(e, np.float64) - 1000.0
            return 20.0 + np.where(np.abs(x) < 50.0, -1.0 - np.cos(np.pi * x / 50.0), 0.0)
        self.fast._ef.roadsys_clear()
        kw = {"follow": True} if follow else {}
        sq = self.fast._ef.roadsys_square(table([seg("r", [[300, 1000], [1700, 1000]], cls=cls, kmh=kmh, bridge=(0.586, 0.614))]), (0, 0),
                                          ground, **kw)
        z = self.fast._ef.roadsys_blend([sq], np.array([[1000.0, 1000.0]]), np.array([[1.0, 0.0]]), ["r"], False)[0]
        return 20.0 - float(z)

    def test_minor_roads_keep_the_dip_majors_do_not_change(self):
        off, on = self.dip_kept(4, 70.0, False), self.dip_kept(4, 70.0, True)
        self.assertGreater(on, 1.6)
        self.assertGreater(on, off + 0.5)
        self.assertEqual(self.dip_kept(1, 110.0, False), self.dip_kept(1, 110.0, True))

    def test_only_where_the_ground_is_not_coarse(self):
        import roadsys
        frame = roadsys.region(40.0, -80.0)[1]
        win = self.fast._ef.roadsys_square_window((0, 0))
        with mock.patch.object(roadsys, "FOLLOW_ON", True):
            with mock.patch.object(roadsys, "COARSE", lambda la, lo: False):
                self.assertTrue(roadsys._follow(frame, win))
            with mock.patch.object(roadsys, "COARSE", lambda la, lo: True):
                self.assertFalse(roadsys._follow(frame, win))
            with mock.patch.object(roadsys, "COARSE", None):
                self.assertFalse(roadsys._follow(frame, win), "no DEM to ask: today's")
        with mock.patch.object(roadsys, "FOLLOW_ON", False), mock.patch.object(roadsys, "COARSE", lambda la, lo: False):
            self.assertFalse(roadsys._follow(frame, win))


if __name__ == "__main__":
    unittest.main()
