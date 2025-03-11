# Pipelines Installation Check

This package demonstrates processing a single CCD with the Rubin Observatory LSST Science Pipelines.
It contains input files and astrometric reference catalogs needed to process the data from a single HSC detector.
Its main purpose is to check that the pipeline infrastructure is working correctly.

## Usage

To run the example, from the `pipelines_check` root directory do:

```
$ source $LSST_HOME/loadLSST.bash
$ setup lsst_distrib
$ setup -j -r .
$ ./bin/run_demo.sh
```

The script creates a new Butler data repository in the `DATA_REPO` subdirectory containing the raw and calibration data found in the `input_data` directory.
It then processes the data using the `pipetask` command to execut the `ProcessCcd` pipeline.
The outputs from processing are written to the `demo_collection` collection.
To rerun the processing you can either delete the `DATA_REPO` subdirectory and run the script again, or else you can copy and run the `pipetask` command and change the output collection.

If you prefer, you can run the demo script by typing `scons`.

## Included Data

The package comes with raw data from detector 10 of visit 903342.
This is an r-band observation

Also included are the required bias/dark/flat calibration frames and a reference catalog.
The master calibrations have been lossy-compressed to save space and so are not expected to be identical to those found in the `testdata_ci_hsc` data package.

## Maintenance

There should not be any need to update the data files themselves.
If the Butler registry schema changes it will be necessary to update the exported registry files to keep them compatible with the new Butler.
This is done by first completing a new run of the `ci_hsc_gen3` package.
With that package setup, the single-ccd subset is exported by running the script `bin/rebuild_demo.sh`.

The dark/bias/flat calibration files are *not* the same as those found in `testdata_ci_hsc`.
They have been lossy-compressed with `fpack -g2` but retaining the `.fits` extension.
They should not be overwritten by the uncompressed versions that will be exported by the `rebuild_demo.sh` script.
Doing so would significantly increase the size of the Git repository.

This script will export data to a `staging` directory.
If there has been no change to the `testdata_ci_hsc` data or to the file templates used for Butler ingest, there should be no need to move the data across from staging.
All that is required is to copy the `export.yaml` file into the `input_data` directory.

If the files moved then the existing files in `input_data` should be moved to the required locations.

If the calibration files really have changed then it will be necessary to recompress them before moving them into the new location in `input_data`.
