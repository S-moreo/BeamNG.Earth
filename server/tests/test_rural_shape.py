"""BNE_ROAD_FOLLOW (roads keep the land's crests and dips) and BNE_RURAL_BANK (country roads bank their bends):
grading.profile_sigma / grading.bank_design / grading.bank with the switches on and off."""
import math
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


def bend(radius, angle_deg=90.0, lead=150.0, step=2.0):
    """A straight lead, a circular bend of radius (m) through angle_deg to the left, a straight lead: (n, 2)."""
    pts = [(x, 0.0) for x in np.arange(-lead, 0.0, step)]
    a = math.radians(angle_deg)
    for t in np.arange(0.0, a, step / radius):
        pts.append((radius * math.sin(t), radius * (1.0 - math.cos(t))))
    end = np.array([radius * math.sin(a), radius * (1.0 - math.cos(a))])
    d = np.array([math.cos(a), math.sin(a)])
    for s in np.arange(step, lead, step):
        pts.append(tuple(end + d * s))
    return np.asarray(pts, np.float64)


class FollowTest(unittest.TestCase):
    def test_off_is_unchanged(self):
        with mock.patch.object(grading, "FOLLOW_ON", False):
            self.assertEqual(grading.profile_sigma(spec("tertiary")), 20.0)
            self.assertEqual(grading.profile_sigma(spec("primary")), grading.SIGMA_MAJOR_M)

    def test_on_shorter_for_minor_classes_majors_kept(self):
        with mock.patch.object(grading, "FOLLOW_ON", True):
            self.assertEqual(grading.profile_sigma(spec("tertiary")), 9.0)
            self.assertEqual(grading.profile_sigma(spec("primary")), 14.0)
            self.assertEqual(grading.profile_sigma(spec("tertiary", link=True)), grading.FOLLOW_LINK_SIGMA_M)
            self.assertEqual(grading.profile_sigma(spec("motorway")), grading.SIGMA_MAJOR_M)
            self.assertEqual(grading.profile_sigma(spec("trunk")), grading.SIGMA_MAJOR_M)
            self.assertEqual(grading.profile_sigma(roads.Spec(4.0, "gravel", False, "track")),
                             grading.DIRT_SIGMA_MINOR_M)      # dirt roads as before

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


class RuralBankTest(unittest.TestCase):
    def test_off_no_bank_below_trunk(self):
        with mock.patch.object(grading, "RURAL_BANK_ON", False):
            self.assertIsNone(grading.bank_design(spec("tertiary")))
            self.assertIsNone(grading.bank(bend(60.0), spec("tertiary"), ext=(1, 1)))
            self.assertIsNotNone(grading.bank_design(spec("motorway")))

    def test_motorway_design_unchanged(self):
        for on in (False, True):
            with mock.patch.object(grading, "RURAL_BANK_ON", on):
                e, r_min, st, ro, fa, sg = grading.bank_design(spec("motorway"))
                self.assertEqual((e, st, ro, fa, sg), (grading.BANK_E_MAX, grading.BANK_STENCIL_M,
                                                       grading.BANK_RUNOFF_M, grading.BANK_FADE_M,
                                                       grading.BANK_SIGMA_M))
                self.assertAlmostEqual(r_min, 110.0 ** 2 / (127.0 * 0.18))

    def test_on_tight_country_bend_leans_in(self):
        with mock.patch.object(grading, "RURAL_BANK_ON", True):
            b = grading.bank(bend(40.0), spec("tertiary"), ext=(1, 1))
        self.assertIsNotNone(b)
        self.assertLess(float(b.min()), -0.07)                # (a left-hand bend: grading's sign, the I-80 test's)
        self.assertLessEqual(float(b.max()), 1e-9)            # one way only
        self.assertLessEqual(float(np.abs(b).max()), grading.RURAL_BANK_E_MAX + 1e-9)
        self.assertLess(abs(float(b[5])), 0.01)               # level on the straight lead

    def test_gentle_bend_leans_less(self):
        with mock.patch.object(grading, "RURAL_BANK_ON", True):
            tight = grading.bank(bend(40.0), spec("tertiary"), ext=(1, 1))
            wide = grading.bank(bend(400.0, 40.0), spec("tertiary"), ext=(1, 1))
        self.assertLess(float(np.abs(wide).max()) if wide is not None else 0.0, float(np.abs(tight).max()) / 2)

    def test_speed_limit_sets_design_speed(self):
        with mock.patch.object(grading, "RURAL_BANK_ON", True):
            slow = grading.bank_design(spec("tertiary", kmh=40.0))[1]
            fast_ = grading.bank_design(spec("tertiary", kmh=90.0))[1]
        self.assertLess(slow, fast_)

    def test_on_not_town_link_or_mountain(self):
        with mock.patch.object(grading, "RURAL_BANK_ON", True):
            self.assertIsNone(grading.bank_design(spec("tertiary", urban=True)))
            self.assertIsNone(grading.bank_design(spec("tertiary", link=True)))
            self.assertIsNone(grading.bank_design(spec("tertiary", mountain=True)))
            self.assertIsNone(grading.bank_design(spec("service")))


if __name__ == "__main__":
    unittest.main()
