#!/bin/bash

export DYLD_LIBRARY_PATH=${LSST_LIBRARY_PATH}

# Exit on command failure
set -e

# Echo commands
set -x

#
# Doing this as a shell script instead of scons to make it
# easier to read.

if [ ! -f DATA_REPO/butler.yaml ]; then
    butler create DATA_REPO
    butler register-instrument DATA_REPO lsst.obs.subaru.HyperSuprimeCam
fi

# Hack assuming posix datastore
if [ ! -d DATA_REPO/HSC/calib ]; then
    butler import DATA_REPO "${PWD}/input_data" --export-file "${PWD}/input_data/export.yaml" --output-run shared/ci_hsc --skip-dimensions instrument,physical_filter,detector
fi

# ingestRaws.py doesn't search recursively; over-specifying to work around that.
if [ -z "$(find -L DATA_REPO/HSC/raw -type f)" ]; then
    butler ingest-raws DATA_REPO --dir input_data/HSC/raw/all/raw/r/HSC-R/
    butler define-visits DATA_REPO -i HSC --collections HSC/raw/all
fi

# Pipeline execution will fail on second attempt because the output run
# can not be the same.
pipetask run -d "exposure=903342 AND detector=10" -j 1 -b DATA_REPO/butler.yaml \
    -i HSC/calib,HSC/raw/all,ref_cats,shared/ci_hsc \
    --register-dataset-types -p "${PIPE_TASKS_DIR}/pipelines/ProcessCcd.yaml" \
    --instrument lsst.obs.subaru.HyperSuprimeCam --output-run demo_collection
