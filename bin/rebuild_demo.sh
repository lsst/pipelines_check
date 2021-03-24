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

# This script should be used solely to regenerate the test data from
# a ci_hsc_gen3 processing.

export DYLD_LIBRARY_PATH=${LSST_LIBRARY_PATH}

#Check that CI_HSC_GEN3_DIR exists, otherwise tell user to set it up.
butler="${CI_HSC_GEN3_DIR}/DATA"

# Generate the graph corresponding to ProcessCCD on a single detector.
pipetask qgraph -p "${PIPE_TASKS_DIR}/pipelines/DRP.yaml#processCcd" \
    --instrument lsst.obs.subaru.HyperSuprimeCam -b "${butler}" \
    -i HSC/calib,HSC/raw/all,HSC/masks,refcats,skymaps \
    -d "visit=903342 AND detector=10" --output make_graph -q single_ccd_graph.qgraph

# This should specify paths so that export.py can be generic
python bin.src/exportGraphInputs.py "${butler}" single_ccd_graph.qgraph
