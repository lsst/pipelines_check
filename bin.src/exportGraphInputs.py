#!/usr/bin/env python

import pickle
import argparse
from lsst.daf.butler import Butler


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export all inputs required to execute a quantum graph.")
    parser.add_argument("butler", help="Directory or butler.yaml to export from")
    parser.add_argument("graph", help="Pickle file containing a quantum graph")
    parser.add_argument("--output", default="export_dir", help="Directory to export to")
    args = parser.parse_args()

    butler = Butler(args.butler)

    with(open(args.graph, "rb")) as f:
        graph = pickle.load(f)

    # dataset_types_to_save = ("brightObjectMask", "ps1_pv3_3pi_20170110", "jointcal_photoCalib",
    #                          "jointcal_wcs", "bias", "dark", "flat", "sky", "raw",
    #                          "camera", "bfKernel")
    dataset_types_to_exclude = ("raw", "postISRCCD", "icExp", "icExpBackground", "icSrc")

    with butler.export(directory=args.output, format="yaml", transfer="auto") as export:
        items = []
        for graph_node in graph:
            for quantum in graph_node.quanta:
                for key, value in quantum.predictedInputs.items():
                    for dataset in value:
                        if dataset.datasetType.name not in dataset_types_to_exclude:
                            # The quantum graph doesn't know the ID of the
                            # real dataset so convert to a real ref
                            found = set(butler.registry.queryDatasets(dataset.datasetType.name,
                                                                      collections=...,
                                                                      dataId=dataset.dataId))
                            items.extend(found)
        export.saveDatasets(items)

    # This is solely to export the raw files. We do not need the yaml
    with butler.export(directory=args.output, filename="junk.yaml", format="yaml", transfer="auto") as export:
        items = []
        for graph_node in graph:
            for quantum in graph_node.quanta:
                for key, value in quantum.predictedInputs.items():
                    for dataset in value:
                        if dataset.datasetType.name in ("raw",):
                            items.append(dataset)
        export.saveDatasets(items)
