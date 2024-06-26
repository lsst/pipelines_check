#!/usr/bin/env python

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

import os
import argparse
from lsst.daf.butler import Butler
from lsst.pipe.base import QuantumGraph


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export all inputs required to execute a quantum graph.")
    parser.add_argument("butler", help="Directory or butler.yaml to export from")
    parser.add_argument("graph", help="Pickle file containing a quantum graph")
    parser.add_argument("--output", default="staging", help="Directory to export to")
    args = parser.parse_args()

    butler = Butler(args.butler)
    graph = QuantumGraph.loadUri(args.graph, universe=butler.dimensions)

    # dataset_types_to_save = ("brightObjectMask", "ps1_pv3_3pi_20170110",
    #                          "jointcal_photoCalib", "jointcal_wcs", "bias",
    #                          "dark", "flat", "sky", "raw",
    #                          "camera", "bfKernel")
    dataset_types_to_exclude = ("raw", "postISRCCD", "icExp", "icExpBackground", "icSrc")

    os.makedirs(args.output, exist_ok=True)
    with butler.export(directory=args.output, format="yaml", transfer="auto") as export:
        items = []
        for quantum_node in graph:
            for datasetType, refs in quantum_node.quantum.inputs.items():
                if datasetType.name not in dataset_types_to_exclude:
                    # The quantum graph may not know the ID of the
                    # real dataset so convert to a real ref
                    for ref in refs:
                        found = set(butler.registry.queryDatasets(datasetType.name, collections=...,
                                                                  dataId=ref.dataId))
                        items.extend(found)
        export.saveDatasets(items)
        export.saveCollection("HSC/calib")

    # This is solely to export the raw files. We do not need the yaml
    with butler.export(directory=args.output, filename="junk.yaml", format="yaml", transfer="auto") as export:
        items = []
        for quantum in graph.findQuantaWithDSType("raw"):
            # Verify that raw is an input and not an output
            if "raw" in quantum.inputs:
                items.extend(quantum.inputs["raw"])
        export.saveDatasets(items)
