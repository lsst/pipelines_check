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
        expected_places = 6
        for name, var, val in [
                ("im_mean", im_mean, 4.38851228731325),
                ("im_std", im_std, 163.46927652023643),
                ("var_mean", var_mean, 53.91476078545389),
                ("var_std", var_std, 52.85387580502370),
                ("num_good_pix", num_good_pix, 7725602),
                ("psf_ixx", psf_ixx, 4.256659271138591),
                ("psf_iyy", psf_iyy, 4.694855952992471),
                ("psf_ixy", psf_ixy, -0.5667379019971804),
                ("summary_psfSigma", summary.psfSigma, 2.1136196194659913),
                ("summary_psfIxx", summary.psfIxx, 4.2751215254309685),
                ("summary_psfIyy", summary.psfIyy, 4.743056930424588),
                ("summary_psfIxy", summary.psfIxy, -0.5653230652801393),
                ("summary_psfArea", summary.psfArea, 76.552791664243),
                ("summary_ra", summary.ra, 320.75894109112244),
                ("summary_decl", summary.decl, -0.2349829603929196),
                ("summary_zenithDistance", summary.zenithDistance, 21.04574994905643),
                ("summary_zeroPoint", summary.zeroPoint, 30.549129811426397),
                ("summary_skyBg", summary.skyBg, 179.0711165368557),
                ("summary_skyNoise", summary.skyNoise, 7.379701984171585),
                ("summary_meanVar", summary.meanVar, 49.844225433895396)
        ]:
            # Uncomment following line to get replacement code when
            # values need updating.
            # print(f'("{name}", {name.replace("_", ".")}, {var:.14f}),')
            self.assertAlmostEqual(var, val, places=expected_places, msg=name)

    def test_background(self):
        """Test background level."""
        bkg = self.butler.get("calexpBackground", detector=self.detector, visit=self.visit)

        bg0_arr = bkg.getImage().array
        bg_mean = bg0_arr.mean(dtype=np.float64)
        bg_std = bg0_arr.std(dtype=np.float64)

        self.assertAlmostEqual(bg_mean, 179.28372409391142, places=7, msg="calexpBackground mean")
        self.assertAlmostEqual(bg_std, 0.8295671365710378, places=7, msg="calexpBackground stddev")

    def test_ic_src(self):
        """Test icSrc catalog."""
        ic_src = self.butler.get("icSrc", detector=self.detector, visit=self.visit)
        self.assertEqual(len(ic_src), 266)

    def test_src(self):
        """Test src catalog."""
        src = self.butler.get("src", detector=self.detector, visit=self.visit)
        self.assertEqual(len(src), 1363)


def setup_module(module):
    lsst.utils.tests.init()


class MemoryTestCase(lsst.utils.tests.MemoryTestCase):
    pass


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
