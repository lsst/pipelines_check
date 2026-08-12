import os
from SCons.Script import SConscript, Environment, Default

# Import sconsUtils here rather than letting bin.src/SConscript be the first
# to do so.  Importing it builds an environment from an optional buildOpts.py
# file, and SCons creates a node for that file even when it is absent, in
# whichever directory is being read.  A node in bin.src would be reported by
# the Glob() that looks for scripts to install.
import lsst.sconsUtils  # noqa: F401

SConscript(os.path.join(".", "bin.src", "SConscript"))

env = Environment(ENV=os.environ)
REPO_ROOT = os.path.abspath("DATA_REPO")
run_demo = env.Command(os.path.join(REPO_ROOT, "shared", "ci_hsc_output"), None,
                       ["bin/run_demo.sh"])

env.Depends(run_demo, "bin")
env.Alias("all", run_demo)
Default(run_demo)
