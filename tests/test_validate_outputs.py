# This file is part of pipelines_check.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Test calexp quantities from pipelines_check test run."""
import os
import unittest
import numpy as np

from lsst.daf.butler import Butler
import lsst.geom as geom
import lsst.utils.tests

TESTDIR = os.path.abspath(os.path.dirname(__file__))

# These collection names must match those used in the run_demo.sh
# script.
MAIN_CHAIN = "demo_collection"


class TestValidateOutputs(lsst.utils.tests.TestCase):
    """Check values from outputs from test run."""
    def setUp(self):
        """Create a new butler root for each test."""
        root = os.path.join(TESTDIR, os.path.pardir, "DATA_REPO")
        self.butler = Butler(root, writeable=False, collections=[MAIN_CHAIN])
        self.detector = 10
        self.visit = 903342

    def test_calexp(self):
        """Test quantities in the calexp."""
        exposure = self.butler.get("calexp", detector=self.detector, visit=self.visit)

        self.assertEqual(exposure.getBBox(),
                         geom.Box2I(geom.Point2I(0, 0), geom.Extent2I(2048, 4176)))
        masked_image = exposure.maskedImage
        num_good_pix = np.sum(masked_image.mask.array == 0)

        image_arr = masked_image.image.array
        im_mean = image_arr.mean(dtype=np.float64)
        im_std = image_arr.std(dtype=np.float64)
        var_arr = masked_image.variance.array
        var_mean = var_arr.mean(dtype=np.float64)
        var_std = var_arr.std(dtype=np.float64)

        summary = exposure.info.getSummaryStats()

        psf = exposure.psf
        psf_avg_pos = psf.getAveragePosition()
        psf_shape = psf.computeShape(psf_avg_pos)
        psf_ixx = psf_shape.getIxx()
        psf_iyy = psf_shape.getIyy()
        psf_ixy = psf_shape.getIxy()

        # NOTE: These values are purely empirical, and need to be
        # updated to reflect major algorithmic changes.
        # If this test fails after an algorithmic change due to
        # small numeric changes here, check on slack at
        # #dm-science-pipelines as to whether the changes are
        # reasonable, and then replace the failing values by
        # running the test to determine the updated values.
        standard_atol = 5e-7
        for name, var, val, atol in [
                ("im_mean", im_mean, 4.41132288593475, standard_atol),
                ("im_std", im_std, 163.46956365298914, standard_atol),
                ("var_mean", var_mean, 51.764979094464934, standard_atol),
                ("var_std", var_std, 48.19498276625069, standard_atol),
                ("num_good_pix", num_good_pix, 7636297.0, 0),
                ("psf_ixx", psf_ixx, 4.267383627670743, 6e-7),
                ("psf_iyy", psf_iyy, 4.688844960286263, 7e-7),
                ("psf_ixy", psf_ixy, -0.5830372248114177, standard_atol),
                ("summary.psfSigma", summary.psfSigma, 2.1137084416932836, standard_atol),
                ("summary.psfIxx", summary.psfIxx, 4.286740805245574, 5.1e-7),
                ("summary.psfIyy", summary.psfIyy, 4.735538416914092, standard_atol),
                ("summary.psfIxy", summary.psfIxy, -0.5823368254962096, standard_atol),
                # TODO: Find a way to tighten psfArea atol in DM-46415.
                ("summary.psfArea", summary.psfArea, 82.62854203870441, 7e-6),
                ("summary.ra", summary.ra, 320.7589338738758, standard_atol),
                ("summary.dec", summary.dec, -0.23498072899127875, standard_atol),
                ("summary.zenithDistance", summary.zenithDistance, 21.045745569180554, standard_atol),
                ("summary.zeroPoint", summary.zeroPoint, 30.54879141025879, 2e-5),
                ("summary.skyBg", summary.skyBg, 179.05450795590878, 7e-6),
                ("summary.skyNoise", summary.skyNoise, 7.379777185851009, standard_atol),
                ("summary.meanVar", summary.meanVar, 47.65954782565453, standard_atol),
        ]:
            # Uncomment following line to get replacement code when
            # values need updating.
            # print(f'("{name}", {name}, {var:.14f}),')
            with self.subTest(name):
                self.assertFloatsAlmostEqual(var, val, atol=atol, rtol=0, msg=name)

    def test_background(self):
        """Test background level."""
        bkg = self.butler.get("calexpBackground", detector=self.detector, visit=self.visit)

        bg0_arr = bkg.getImage().array
        bg_mean = bg0_arr.mean(dtype=np.float64)
        bg_std = bg0_arr.std(dtype=np.float64)

        for name, var, val in (
                ("calexpBackground mean", bg_mean, 179.2608874980628),
                ("calexpBackground stddev", bg_std, 0.8222624653543368),
        ):
            with self.subTest(name):
                self.assertFloatsAlmostEqual(var, val, atol=5e-7, msg=name)

    def test_initial_psf_stars(self):
        """Test icSrc catalog."""
        initial_psf_stars = self.butler.get("initial_psf_stars_detector", detector=self.detector,
                                            visit=self.visit)
        self.assertEqual(len(initial_psf_stars), 266)

    def test_src(self):
        """Test src catalog."""
        src = self.butler.get("src", detector=self.detector, visit=self.visit)
        self.assertEqual(len(src), 1357)


def setup_module(module):
    lsst.utils.tests.init()


class MemoryTestCase(lsst.utils.tests.MemoryTestCase):
    pass


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
