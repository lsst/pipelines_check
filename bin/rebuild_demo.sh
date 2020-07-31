#!/bin/bash

export DYLD_LIBRARY_PATH=${LSST_LIBRARY_PATH}

#Check that CI_HSC_GEN3_DIR exists, otherwise tell user to set it up.
butler="${CI_HSC_GEN3_DIR}/DATA"

# Generate the graph corresponding to ProcessCCD on a single detector.
pipetask qgraph -p "${PIPE_TASKS_DIR}/pipelines/ProcessCcd.yaml" \
    --instrument lsst.obs.subaru.HyperSuprimeCam -b "${butler}" \
    -i HSC/calib,HSC/raw/all,HSC/masks,ref_cats,skymaps,shared/ci_hsc \
    -d "visit=903342 AND detector=10" --output make_graph -q single_ccd_graph.pkl

# This should specify paths so that export.py can be generic
python bin.src/exportGraphInputs.py "${butler}" single_ccd_graph.pkl
