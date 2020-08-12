import os
from SCons.Script import SConscript, Environment, Default
SConscript(os.path.join(".", "bin.src", "SConscript"))

env = Environment(ENV=os.environ)
REPO_ROOT = os.path.abspath("DATA_REPO")
run_demo = env.Command(os.path.join(REPO_ROOT, "shared", "ci_hsc_output"), None,
                       ["bin/run_demo.sh"])

env.Alias("all", run_demo)
Default(run_demo)
