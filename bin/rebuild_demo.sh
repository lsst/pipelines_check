#!/bin/bash

export DYLD_LIBRARY_PATH=${LSST_LIBRARY_PATH}

#Check that CI_HSC_GEN3_DIR exists, otherwise tell user to set it up.

# Generate the graph corresponding to ProcessCCD on a single detector.
pipetask qgraph -p $PIPE_TASKS_DIR/pipelines/ProcessCcd.yaml \
    --instrument lsst.obs.subaru.HyperSuprimeCam -b $CI_HSC_GEN3_DIR/DATA/butler.yaml \
    -i calib/hsc,raw/hsc,masks/hsc,ref_cats,skymaps,shared/ci_hsc \
    -d "visit=903342 AND detector=10" --output make_graph -q single_ccd_graph.pkl

# This should specify paths so that export.py can be generic
bin/exportGraphInputs.py $CI_HSC_GEN3_DIR/DATA/butler.yaml single_ccd_graph.pkl 

