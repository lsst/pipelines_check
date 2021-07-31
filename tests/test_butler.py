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

"""Output butler from pipelines_check test run."""

import os
import unittest

from lsst.daf.butler import Butler

TESTDIR = os.path.abspath(os.path.dirname(__file__))

# These collection names must match those used in the run_demo.sh
# script.
MAIN_CHAIN = "demo_collection"
EXE_CHAIN = "demo_collection_exe"


class PiplinesCheckTestCase(unittest.TestCase):
    """Check outputs from test run."""

    def setUp(self):
        """Create a new butler root for each test."""
        root = os.path.join(TESTDIR, os.path.pardir, "DATA_REPO")
        self.butler = Butler(root, writeable=False)

    def _get_datasets_from_chain(self, chain, datasetType=...):
        """Return all the datasets from the first run in chain.

        Datasets are all unresolved.
        """
        collections = list(self.butler.registry.queryCollections(chain, flattenChains=True))
        run = collections.pop(0)
        print(f"Retrieving datasets from run {run}")

        unresolved = {ref.unresolved() for ref in self.butler.registry.queryDatasets(datasetType=datasetType,
                                                                                     collections=run)}
        return unresolved

    def testExecutionButler(self):
        """Check outputs match in both runs."""

        # Check that we have identical datasets in both collections
        # except for the dataset.id
        main_datasets = self._get_datasets_from_chain(MAIN_CHAIN)
        exe_datasets = self._get_datasets_from_chain(EXE_CHAIN)
        self.assertGreater(len(exe_datasets), 0)
        self.assertEqual(len(main_datasets), len(exe_datasets))

        difference = main_datasets - exe_datasets
        self.assertEqual(len(difference), 0, "Some datasets missing.")

    def testExecutionExistence(self):
        """Check that the execution butler files are really there."""

        exe_datasets = self._get_datasets_from_chain(EXE_CHAIN)
        for ref in exe_datasets:
            self.assertTrue(self.butler.datasetExists(ref, collections=EXE_CHAIN))

    def testLogDataset(self):
        """Ensure that the logs are captured in both modes."""

        log_datasets = self._get_datasets_from_chain(MAIN_CHAIN, datasetType="isr_log")
        self.assertEqual(len(log_datasets), 1)

        isr_log_ref = log_datasets.pop()

        # Get the logs from both main and exe collections.
        main_isr_log = self.butler.get("isr_log", dataId=isr_log_ref.dataId, collections=MAIN_CHAIN)
        exe_isr_log = self.butler.get("isr_log", dataId=isr_log_ref.dataId, collections=EXE_CHAIN)

        # Timestamps and durations will differ but check to see that the
        # number of log messages matched.
        self.assertEqual(len(main_isr_log), len(exe_isr_log),
                         f"Standard log: {main_isr_log}\n vs\nExecution butler log: {exe_isr_log}")


if __name__ == "__main__":
    unittest.main()
