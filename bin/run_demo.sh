#!/bin/bash

# Exit on command failure
set -e

# Echo commands
set -x

# 
# Doing this as a shell script instead of scons to make it
# easier to read.

if [ ! -f DATA_REPO/butler.yaml ]; then
    makeButlerRepo.py DATA_REPO
fi

bin/ingestExternalData.py DATA_REPO $PWD/export_dir/export.yaml

# ingestRaws.py doesn't search recursively; over-specifying to work around that.
bin/ingestRaws.py DATA_REPO export_dir/raw/hsc/raw/r/HSC-R/903342/

# originally: -i calib/hsc,raw/hsc,masks/hsc,ref_cats,skymaps,shared/ci_hsc 
pipetask run -d "visit=903342 AND detector=10" -j 1 -b DATA_REPO/butler.yaml \
    -i calib/hsc,raw/hsc,ref_cats,shared/ci_hsc \
    --register-dataset-types -p $PIPE_TASKS_DIR/pipelines/ProcessCcd.yaml \
    --instrument lsst.obs.subaru.HyperSuprimeCam -o demo_collection
