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


if [ ! -d DATA_REPO/calib ]; then
    bin/ingestExternalData.py DATA_REPO $PWD/export_dir/export.yaml
fi

# ingestRaws.py doesn't search recursively; over-specifying to work around that.
if [ -z "$(find -L DATA_REPO/raw -type f)" ]; then
    bin/ingestRaws.py DATA_REPO export_dir/raw/hsc/raw/r/HSC-R/903342/
fi

# I dropped the masks/hsc and skymaps collections; apparently they weren't
# needed for this graph so they weren't exported?
# Also this will fail upon re-running, because it wants `--extend-run` if and
# only if the output run already exists.
pipetask run -d "visit=903342 AND detector=10" -j 1 -b DATA_REPO/butler.yaml \
    -i calib/hsc,raw/hsc,ref_cats,shared/ci_hsc \
    --register-dataset-types -p $PIPE_TASKS_DIR/pipelines/ProcessCcd.yaml \
    --instrument lsst.obs.subaru.HyperSuprimeCam --output-run demo_collection 

