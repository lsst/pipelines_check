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
if [ -z "$(butler query-datasets DATA_REPO/ raw | grep HSC)" ]; then
    butler ingest-raws DATA_REPO input_data/HSC/raw/all/raw/r/HSC-R/ --transfer direct
    butler define-visits DATA_REPO HSC --collections HSC/raw/all
fi

incoll="HSC/calib,HSC/raw/all,refcats"

# Pipeline execution will fail on second attempt because the output run
# can not be the same.
# Do not specify a number of processors (-j) to test that the default value
# works.
# The output collection name must match that used in the Python tests.
pipetask --long-log run -d "exposure=903342 AND detector=10" -b DATA_REPO/butler.yaml \
    --input "$incoll" \
    --register-dataset-types -p "${PIPE_TASKS_DIR}/pipelines/DRP.yaml#processCcd" \
    --instrument lsst.obs.subaru.HyperSuprimeCam --output-run demo_collection

# Do not provide a data query (-d) to verify code correctly handles an empty
# query.
pipetask qgraph -b DATA_REPO/butler.yaml \
    --input "$incoll" \
    -p "${PIPE_TASKS_DIR}/pipelines/DRP.yaml#processCcd" \
    --instrument lsst.obs.subaru.HyperSuprimeCam --output-run demo_collection_1

# Do a new shorter run using replace-run
pipetask run -d "exposure=903342 AND detector=10" -b DATA_REPO/butler.yaml \
    --input "$incoll" \
    --register-dataset-types -p "${PIPE_TASKS_DIR}/pipelines/DRP.yaml#isr" \
    --instrument lsst.obs.subaru.HyperSuprimeCam --output demo_collection2

pipetask run -d "exposure=903342 AND detector=10" -b DATA_REPO/butler.yaml \
    --register-dataset-types -p "${PIPE_TASKS_DIR}/pipelines/DRP.yaml#isr" \
    --instrument lsst.obs.subaru.HyperSuprimeCam --output demo_collection2 --replace-run

# Test the execution butler.
# Create execution butler with new graph and output collection.

graph_file="test_exe.qgraph"
exedir="./execution_butler"
# This collection name must match that used in the Python tests.
exeoutput="demo_collection_exe"
exerun="$exeoutput/YYYYMMDD"

pipetask qgraph -b DATA_REPO/butler.yaml \
    --input "$incoll" \
    -p "${PIPE_TASKS_DIR}/pipelines/DRP.yaml#processCcd" \
    -q "$graph_file" \
    --save-execution-butler "$exedir" \
    --clobber-execution-butler \
    --instrument lsst.obs.subaru.HyperSuprimeCam --output "$exeoutput" --output-run "$exerun"

# Run the execution butler in multiple steps, ensuring that a fresh
# butler is used each time.

tmp_butler="./tmp_execution_butler"
refresh_exe() {
  rm -rf "$tmp_butler"
  mkdir "$tmp_butler"
  cp "$exedir"/* "$tmp_butler/"
}

refresh_exe

# Run the init step
pipetask --long-log run -b "$tmp_butler" -i "$incoll" --output-run "$exerun" --init-only --register-dataset-types --qgraph "$graph_file" --extend-run

# Run the three quanta one at a time to ensure that we can start from a
# clean execution butler every time.
refresh_exe
node=0
pipetask --long-log run -b "$tmp_butler" --output-run "$exerun" --qgraph "$graph_file" --qgraph-node-id "$node" --skip-init-writes --extend-run --clobber-outputs --skip-existing

refresh_exe
node=1
pipetask --long-log run -b "$tmp_butler" --output-run "$exerun" --qgraph "$graph_file" --qgraph-node-id $node --skip-init-writes --extend-run --clobber-outputs --skip-existing

refresh_exe
node=2
pipetask --long-log run -b "$tmp_butler" --output-run "$exerun" --qgraph "$graph_file" --qgraph-node-id $node --skip-init-writes --extend-run --clobber-outputs --skip-existing

# Bring home the datasets.
butler --log-level=VERBOSE --long-log transfer-datasets "$exedir" DATA_REPO --collections "$exerun"

# Create the collection in the main repo.
# Do this by first appending the input collections and then prepending
# the output run collection. This way we do not need to check for existence
# of a previous chain.
# If --replace-run is required an extra line to do --mode=pop should be added.
butler collection-chain DATA_REPO --mode=extend "$exeoutput" ${incoll//,/ }
butler collection-chain DATA_REPO --mode=prepend "$exeoutput" "$exerun"

# Run some tests on the final butler state.
pytest tests/
