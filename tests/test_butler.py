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
from lsst.pipe.base import TaskMetadata

TESTDIR = os.path.abspath(os.path.dirname(__file__))

# These collection names must match those used in the run_demo.sh
# script.
MAIN_CHAIN = "demo_collection"
EXE_CHAIN = "demo_collection_exe"
QBB_CHAIN = "demo_collection_qbb"


class PiplinesCheckTestCase(unittest.TestCase):
    """Check outputs from test run."""

    def setUp(self):
        """Create a new butler root for each test."""
        root = os.path.join(TESTDIR, os.path.pardir, "DATA_REPO")
        self.butler = Butler(root, writeable=False)

    def _get_datasets_from_chain(self, chain, datasetType=...):
        """Return all the datasets from the first run in chain.
        """
        collections = list(self.butler.registry.queryCollections(chain, flattenChains=True))
        # Choose the collection to query, and query datasets in that
        # collection.
        # The collection to query datasets from will be named "demo_collection"
        # or "demo_collection_exe/YYYMMDD" (the exe collection is inserted in
        # run_demo.sh). Collections will only contain one or the other (and no
        # other collections named "demo_colleciton") so it is enough to just
        # find the one with the name that contains "demo_collection" and use
        # search it to resolve the other datasets.
        run = next(c for c in collections if "demo_collection" in c)
        collections.remove(run)
        print(f"Retrieving datasets from run {run}")

        refs = set(self.butler.registry.queryDatasets(datasetType=datasetType, collections=run))
        return refs

    def testMetadata(self):
        """Test that metadata can be retrieved."""

        dataId = {"instrument": "HSC", "visit": 903342, "detector": 10}
        collection = "demo_collection"

        cal = self.butler.get("calibrateImage_metadata", dataId=dataId, collections=collection)
        isr = self.butler.get("isr_metadata", dataId=dataId, collections=collection, exposure=903342)

        self.assertIsInstance(cal, TaskMetadata)
        self.assertIsInstance(isr, TaskMetadata)

        # Check that they both have a quantum entry.
        self.assertIn("quantum.startUtc", isr)

        # PropertySet.__contains__ does not support "."
        self.assertIn("quantum.startUtc", cal)

    def testExecutionButler(self):
        """Check outputs match in both runs."""

        for chain in (EXE_CHAIN, QBB_CHAIN):
            with self.subTest(chain=chain):
                # Check that we have identical datasets in both collections
                # except for the dataset.id
                main_datasets = self._get_datasets_from_chain(MAIN_CHAIN)
                datasets = self._get_datasets_from_chain(chain)
                self.assertGreater(len(datasets), 0)
                self.assertEqual(len(main_datasets), len(datasets))

                # Extract dataset type and DataIds for comparison.
                main_data_ids = {(ref.datasetType, ref.dataId) for ref in main_datasets}
                data_ids = {(ref.datasetType, ref.dataId) for ref in datasets}

                difference = main_data_ids - data_ids
                self.assertEqual(len(difference), 0, "Some datasets missing.")

    def testExecutionExistence(self):
        """Check that the execution butler files are really there."""

        for chain in (EXE_CHAIN, QBB_CHAIN):
            with self.subTest(chain=chain):
                datasets = self._get_datasets_from_chain(chain)
                for ref in datasets:
                    self.assertTrue(self.butler.exists(ref))

    def testLogDataset(self):
        """Ensure that the logs are captured in both modes."""

        log_datasets = self._get_datasets_from_chain(MAIN_CHAIN, datasetType="isr_log")
        self.assertEqual(len(log_datasets), 1)

        isr_log_ref = log_datasets.pop()

        # Get the logs from both main and exe/qbb collections.
        main_isr_log = self.butler.get("isr_log", dataId=isr_log_ref.dataId, collections=MAIN_CHAIN)
        for chain in (EXE_CHAIN, QBB_CHAIN):
            with self.subTest(chain=chain):
                isr_log = self.butler.get("isr_log", dataId=isr_log_ref.dataId, collections=chain)

                # Timestamps and durations will differ but check to see that
                # the number of log messages matched.
                self.assertEqual(
                    len(main_isr_log),
                    len(isr_log),
                    f"Standard log: {main_isr_log}\n vs\nExecution butler log: {isr_log}"
                )


if __name__ == "__main__":
    unittest.main()
