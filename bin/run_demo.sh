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

# Explicitly define a dataset type that uses the old style metadata definition.
if [ -z "$(butler query-dataset-types DATA_REPO/ calibrate_metadata | grep -v results)"]; then
    butler register-dataset-type DATA_REPO calibrate_metadata PropertySet band instrument detector physical_filter visit
fi

incoll="HSC/calib,HSC/raw/all,refcats"
pipeline="${DRP_PIPE_DIR}/pipelines/HSC/pipelines_check.yaml"

# Pipeline execution will fail on second attempt because the output run
# can not be the same.
# Do not specify a number of processors (-j) to test that the default value
# works.
# The output collection name must match that used in the Python tests.
pipetask --long-log run -d "exposure=903342 AND detector=10" -b DATA_REPO/butler.yaml \
    --input "$incoll" \
    --register-dataset-types -p "$pipeline" \
    --instrument lsst.obs.subaru.HyperSuprimeCam --output-run demo_collection

# Do not provide a data query (-d) to verify code correctly handles an empty
# query.
pipetask qgraph -b DATA_REPO/butler.yaml \
    --input "$incoll" \
    -p "$pipeline" \
    --instrument lsst.obs.subaru.HyperSuprimeCam --output-run demo_collection_1

# Do a new shorter run using replace-run
pipetask run -d "exposure=903342 AND detector=10" -b DATA_REPO/butler.yaml \
    --input "$incoll" \
    --register-dataset-types -p "$pipeline#isr" \
    --instrument lsst.obs.subaru.HyperSuprimeCam --output demo_collection2

pipetask run -d "exposure=903342 AND detector=10" -b DATA_REPO/butler.yaml \
    --register-dataset-types -p "$pipeline#isr" \
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
    -p "$pipeline" \
    -q "$graph_file" \
    --save-execution-butler "$exedir" \
    --clobber-execution-butler \
    --instrument lsst.obs.subaru.HyperSuprimeCam --output "$exeoutput" --output-run "$exerun"

# Run the execution butler in multiple steps, ensuring that a fresh
# butler is used each time.
refresh_butler() {
  rm -rf "$1"
  mkdir "$1"
  cp "$exedir"/* "$1/"
}

# Run the init step
TMP_BUTLER="./tmp_execution_butler"
refresh_butler $TMP_BUTLER
pipetask --long-log run -b "$TMP_BUTLER" -i "$incoll" --output-run "$exerun" --init-only --register-dataset-types --qgraph "$graph_file" --extend-run

# Run the three quanta one at a time to ensure that we can start from a
# clean execution butler every time.
for NODE in $(pipetask qgraph -b "$TMP_BUTLER" -g "$graph_file" --show-qgraph-header \
    |jq -r 'first(.Nodes)[][0]')
do
  # Run the execution butler in multiple steps, ensuring that a fresh
  # butler is used each time.
  TMP_BUTLER_NODE="./tmp_execution_butler-$NODE"
  refresh_butler $TMP_BUTLER_NODE

  # Run these three pipetasks concurrently
  pipetask --long-log run -b "$TMP_BUTLER_NODE" --output-run "$exerun" --qgraph "$graph_file" --qgraph-node-id "$NODE" --skip-init-writes --extend-run --clobber-outputs --skip-existing
done

rm -rf ./tmp_execution_butler-*
rm -rf $TMP_BUTLER

# Bring home the datasets.
butler --log-level=VERBOSE --long-log transfer-datasets "$exedir" DATA_REPO --collections "$exerun"

# Create the collection in the main repo.
# Do this by first appending the input collections and then prepending
# the output run collection. This way we do not need to check for existence
# of a previous chain.
# If --replace-run is required an extra line to do --mode=pop should be added.
butler collection-chain DATA_REPO --mode=extend "$exeoutput" "$incoll"
butler collection-chain DATA_REPO --mode=prepend "$exeoutput" "$exerun"

# Test Quantum-backed butler, this will be a replacement for execution butler,
# but for now we test them both, they should produce identical outputs going
# to separate collections.

graph_file="test_qbb.qgraph"
# This collection name must match that used in the Python tests
output_chain="demo_collection_qbb"
output_run="$output_chain/YYYYMMDD"

pipetask qgraph -b DATA_REPO/butler.yaml \
    --input "$incoll" \
    -p "$pipeline" \
    -q "$graph_file" \
    --qgraph-datastore-records \
    --instrument lsst.obs.subaru.HyperSuprimeCam \
    --output "$output_chain" \
    --output-run "$output_run"

# Run the init step
pipetask --long-log pre-exec-init-qbb "DATA_REPO/butler.yaml" "$graph_file"

# Run the three quanta one at a time to ensure that we can start from a
# clean execution butler every time.
for NODE in $(pipetask qgraph -b "DATA_REPO/butler.yaml" -g "$graph_file" --show-qgraph-header \
    |jq -r 'first(.Nodes)[][0]')
do
    pipetask --long-log run-qbb --qgraph-node-id "$NODE" "DATA_REPO/butler.yaml" "$graph_file"
done

# Bring home the datasets, --update-output-chain also creates output chain
# collection from metadata stored in a graph.
butler --log-level=VERBOSE --long-log transfer-from-graph --update-output-chain "$graph_file" DATA_REPO

# Run some tests on the final butler state.
pytest tests/
