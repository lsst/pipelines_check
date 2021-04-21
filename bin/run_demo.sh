#!/bin/bash

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

export DYLD_LIBRARY_PATH=${LSST_LIBRARY_PATH}

# Exit on command failure
set -e

# Echo commands
set -x

# Doing this as a shell script instead of scons to make it
# easier to read.

if [ ! -f DATA_REPO/butler.yaml ]; then
    butler create --seed-config "${PIPELINES_CHECK_DIR}/configs/butler-seed.yaml" DATA_REPO
    butler register-instrument DATA_REPO lsst.obs.subaru.HyperSuprimeCam
fi

# Hack assuming posix datastore
if [ ! -d DATA_REPO/HSC/calib ]; then
    butler import DATA_REPO "${PWD}/input_data" --export-file "${PWD}/input_data/export.yaml" --skip-dimensions instrument,physical_filter,detector
fi

# ingestRaws.py doesn't search recursively; over-specifying to work around that.
if [ -z "$(find -L DATA_REPO/HSC/raw -type f)" ]; then
    butler ingest-raws DATA_REPO input_data/HSC/raw/all/raw/r/HSC-R/
    butler define-visits DATA_REPO HSC --collections HSC/raw/all
fi

# Pipeline execution will fail on second attempt because the output run
# can not be the same.
# Do not specify a number of processors (-j) to test that the default value
# works.
pipetask --long-log run -d "exposure=903342 AND detector=10" -b DATA_REPO/butler.yaml \
    --input HSC/calib,HSC/raw/all,refcats \
    --register-dataset-types -p "${PIPE_TASKS_DIR}/pipelines/DRP.yaml#processCcd" \
    --instrument lsst.obs.subaru.HyperSuprimeCam --output-run demo_collection

# Do not provide a data query (-d) to verify code correctly handles an empty
# query.
pipetask qgraph -b DATA_REPO/butler.yaml \
    --input HSC/calib,HSC/raw/all,refcats \
    -p "${PIPE_TASKS_DIR}/pipelines/DRP.yaml#processCcd" \
    --instrument lsst.obs.subaru.HyperSuprimeCam --output-run demo_collection_1

# Do a new shorter run using replace-run
pipetask run -d "exposure=903342 AND detector=10" -b DATA_REPO/butler.yaml \
    --input HSC/calib,HSC/raw/all,refcats \
    --register-dataset-types -p "${PIPE_TASKS_DIR}/pipelines/DRP.yaml#isr" \
    --instrument lsst.obs.subaru.HyperSuprimeCam --output demo_collection2

pipetask run -d "exposure=903342 AND detector=10" -b DATA_REPO/butler.yaml \
    --register-dataset-types -p "${PIPE_TASKS_DIR}/pipelines/DRP.yaml#isr" \
    --instrument lsst.obs.subaru.HyperSuprimeCam --output demo_collection2 --replace-run
