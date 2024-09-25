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
                ("im_mean", im_mean, 4.3885845565891, standard_atol),
                ("im_std", im_std, 163.46922027517536, standard_atol),
                ("var_mean", var_mean, 51.764979094464934, standard_atol),
                ("var_std", var_std, 48.19498276625069, standard_atol),
                ("num_good_pix", num_good_pix, 7725755.00000000000000, 0),
                ("psf_ixx", psf_ixx, 4.253191896391297, 6e-7),
                ("psf_iyy", psf_iyy, 4.687397483153177, 7e-7),
                ("psf_ixy", psf_ixy, -0.57911628487574, standard_atol),
                ("summary.psfSigma", summary.psfSigma, 2.11203591780044, standard_atol),
                ("summary.psfIxx", summary.psfIxx, 4.272794013403168, 5.1e-7),
                ("summary.psfIyy", summary.psfIyy, 4.735316824053334, standard_atol),
                ("summary.psfIxy", summary.psfIxy, -0.57899030354606, standard_atol),
                # TODO: Find a way to tighten psfArea atol in DM-46415.
                ("summary.psfArea", summary.psfArea, 82.65495879853161, 7e-6),
                ("summary.ra", summary.ra, 320.75894004802291, standard_atol),
                ("summary.dec", summary.dec, -0.23498192412129, standard_atol),
                ("summary.zenithDistance", summary.zenithDistance, 21.04574864469552, standard_atol),
                ("summary.zeroPoint", summary.zeroPoint, 30.548692694925332, standard_atol),
                ("summary.skyBg", summary.skyBg, 179.06974010169506, standard_atol),
                ("summary.skyNoise", summary.skyNoise, 7.379652920569057, standard_atol),
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
                ("calexpBackground mean", bg_mean, 179.2836464883374),
                ("calexpBackground stddev", bg_std, 0.8296105383233686),
        ):
            with self.subTest(name):
                self.assertAlmostEqual(var, val, places=7, msg=name)

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
