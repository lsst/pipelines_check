# Pipelines Installation Check

This package demonstrates processing a single CCD with the Rubin Observatory
science pipelines.

## Usage

Running the script `bin/run_demo.sh` will create a new data repository in the
`DATA_REPO/` dir, ingest the required data from `export_dir`, and process them
with the ProcessCcd pipeline. This script can also be called by running `scons`.

## Maintenance

The data in `export_dir/` is derived from the `ci_hsc_gen3` package. When
`ci_hsc_gen3` is available, the single-ccd subset is exported by running the
script `bin/rebuild_demo.sh`. The exported data is designed so that most demo
users will not need to download the much larger `testdata_ci_hsc` package; the data
in this demo package should be entirely self-contained.

The bias/flat/dark files have been lossy compressed using `fpack -g2` but
retain the `.fits` extension.  After running the rebuild script the new
FITS files should not be committed since they will not be changed from
before (they initially come from `testdata_ci_hsc`) but the original files
may need to be renamed if the collection or template has changed.
