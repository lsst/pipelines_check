# This file is part of pipelines_check.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import numpy as np

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT
from scipy.spatial import cKDTree


class PipelinesCheckTaskConnections(pipeBase.PipelineTaskConnections,
                                    dimensions=("instrument", "visit", "detector")):

    sourceCat = cT.Input(
        doc="Input processed source catalog to test.",
        name="src",
        storageClass="SourceCatalog",
        dimensions=["instrument", "visit", "detector"],
    )

    comparisonCat = cT.Input(
        doc="Comparison source catalog.",
        name="src_comparison",
        storageClass="SourceCatalog",
        dimensions=["instrument", "visit", "detector"],
    )


class PipelinesCheckTaskConfig(pipeBase.PipelineTaskConfig,
                               pipelineConnections=PipelinesCheckTaskConnections):

    doRaise = pexConfig.Field(
        dtype=bool,
        default=True,
        doc="Raise exception if comparison criteria are not met.",
    )
    maxFractionalDiff = pexConfig.Field(
        dtype=float,
        default=0.01,
        doc="Source measurement values must differ by less than this fraction from the comparison catalog",
    )
    maxOutlierFraction = pexConfig.Field(
        dtype=float,
        default=0.01,
        doc="No more than maxOutlierFraction of sources may differ from the comparison catalog",
    )
    maxMissingSourcesFraction = pexConfig.Field(
        dtype=float,
        default=0.01,
        doc="No more than maxMissingSourcesFraction of sources from the comparison catalog may be missing.",
    )
    maxSearchRadiusPixels = pexConfig.Field(
        dtype=float,
        default=2.0,
        doc="Sources are matched if they are within maxSearchRadiusPixels of a comparison catalog source."
    )


class PipelinesCheckTask(pipeBase.PipelineTask):
    """
    Given an input sourceCat Catalog to test and a comparisonCat as the
    "standard" for comparison, this task positionally matches all sources in
    the two catalogs and checks that all floating point column values are
    within a specified fractional tolerance of the comparisonCat value.

    If doRaise is set, an exception is thrown if any discrepancies exceed the
    tolerance. No other output is produced.

    """

    ConfigClass = PipelinesCheckTaskConfig
    _DefaultName = "pipelinesCheck"
    RunnerClass = pipeBase.ButlerInitializedTaskRunner

    def runQuantum(self, butlerQC, inputRefs, outputRefs):
        inputs = butlerQC.get(inputRefs)
        self.run(**inputs)

    @pipeBase.timeMethod
    def run(self, sourceCat, comparisonCat):
        sourceCat_pd = sourceCat.asAstropy()
        comparisonCat_pd = comparisonCat.asAstropy()

        kd_tree = cKDTree(np.stack((sourceCat_pd['base_SdssCentroid_x'],
                                    sourceCat_pd['base_SdssCentroid_y']), axis=1))
        neighbor_dists, neighbor_idx = kd_tree.query(np.stack((comparisonCat_pd['base_SdssCentroid_x'],
                                                              comparisonCat_pd['base_SdssCentroid_y']),
                                                              axis=1),
                                                     k=1,
                                                     distance_upper_bound=self.config.maxSearchRadiusPixels)
        matched_sourceCat_idx = neighbor_idx[neighbor_idx != kd_tree.n]
        matched_comparisonCat_idx = np.arange(len(comparisonCat_pd))[neighbor_idx != kd_tree.n]

        unmatched_fraction = np.sum(neighbor_idx == kd_tree.n)/len(comparisonCat_pd)
        if(unmatched_fraction > self.config.maxMissingSourcesFraction):
            err_msg = "Unmatched sources fraction {:.3f} exceeds maxMissingSourcesFraction ({:.3f})"
            raise RuntimeError(err_msg.format(unmatched_fraction, self.config.maxMissingSourcesFraction))

        # Compare all float columns,
        column_names = list(name for name, col in sourceCat_pd.columns.items()
                            if col.dtype == np.float)
        self.log.info("Comparing {:d} float columns".format(len(column_names)))

        for column in column_names:
            delta = np.abs(sourceCat_pd[column][matched_sourceCat_idx]
                           - comparisonCat_pd[column][matched_comparisonCat_idx])
            with np.errstate(divide="ignore", invalid="ignore"):
                fractional_difference = delta/np.abs(comparisonCat_pd[column][matched_comparisonCat_idx])
            n_discrepancies = np.sum(fractional_difference
                                     > self.config.maxFractionalDiff)

            outlier_fraction = n_discrepancies/len(matched_sourceCat_idx)
            if(outlier_fraction > self.config.maxOutlierFraction):
                raise RuntimeError(f"Catalog discrepancies for column {column} exceed maxFractionalDiff")

            log_msg = "Column {:s} discrepant fraction {:0.3f} ({:d} sources out of {:d})"
            self.log.debug(log_msg.format(column, outlier_fraction, n_discrepancies,
                                          len(matched_sourceCat_idx)))
