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
if [ -z "$(butler query-datasets --collections "*" DATA_REPO/ raw | grep HSC)" ]; then
    butler ingest-raws DATA_REPO input_data/HSC/raw/all/raw/r/HSC-R/ --transfer direct
    butler define-visits DATA_REPO HSC --collections HSC/raw/all
fi

# Explicitly define a dataset type that uses the old style metadata definition.
if [ -z "$(butler query-dataset-types DATA_REPO/ calibrateImage_metadata | grep -v results)" ]; then
    butler register-dataset-type DATA_REPO calibrateImage_metadata PropertySet band instrument detector physical_filter visit
fi

# Make a chain for inputs to be able to test output chain is flattened.
butler collection-chain DATA_REPO HSC/defaults HSC/calib,HSC/raw/all,refcats

incoll="HSC/defaults"
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

# Run the execution butler in multiple steps, ensuring that a fresh
# butler is used each time.
refresh_butler() {
  rm -rf "$1"
  mkdir "$1"
  cp "$exedir"/* "$1/"
}

check_transfer_count() {
  IFS= read -r line;
  echo $line | awk -v expected=$1 -F ':' '{print $0; if (int($2) != int(expected)) {print "Transfer rest count (" int($2) ") != expected (" int(expected) ")"; exit 1}}' 
}

test_quantum_butler() {
  # Test Quantum-backed butler.

  graph_file="test_qbb.qg"
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

  # Run each pipeline step in turn.
  for NODE in $(pipetask qgraph -b "DATA_REPO/butler.yaml" -g "$graph_file" --show workflow \
    | sed -nE 's/^Quantum ([a-z0-9\-]+):.*$/\1/p')
  do
      pipetask --long-log run-qbb -j 2 --qgraph-node-id "$NODE" "DATA_REPO/butler.yaml" "$graph_file"
  done

  # Bring home the datasets, --update-output-chain also creates output chain
  # collection from metadata stored in a graph. Ingest some via a zip file.
  output=$(butler --log-level=VERBOSE --long-log zip-from-graph "$graph_file" DATA_REPO ./ -d "cal*")
  echo $output
  zip_path=$(echo $output | grep .zip | awk -F/ {'print $NF'})
  butler ingest-zip DATA_REPO $zip_path

  # Transfer nothing (because calexp already ingested via zip), don't ask to update chain.
  butler --log-level=VERBOSE --long-log transfer-from-graph -d calexp "$graph_file" DATA_REPO  | check_transfer_count 0
  python tests/check_update_chain.py DATA_REPO "$output_run" "$output_chain" 0

  # Transfer one, don't ask to update chain.
  butler --log-level=VERBOSE --long-log transfer-from-graph -d postISRCCD "$graph_file" DATA_REPO | check_transfer_count 1
  python tests/check_update_chain.py DATA_REPO "$output_run" "$output_chain" 0

  # Transfer nothing (because calexp already ingested via zip), ask to update chain.
  butler --log-level=VERBOSE --long-log transfer-from-graph -d calexp --update-output-chain "$graph_file" DATA_REPO | check_transfer_count 0
  python tests/check_update_chain.py DATA_REPO $output_run $output_chain 1

  # Transfer rest (should be 11) and make sure still in chain.
  butler --log-level=VERBOSE --long-log transfer-from-graph --update-output-chain "$graph_file" DATA_REPO | check_transfer_count 11 
  python tests/check_update_chain.py DATA_REPO $output_run $output_chain 1
}

test_quantum_butler

# Run some tests on the final butler state.
pytest tests/
