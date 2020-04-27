import os
from SCons.Script import SConscript, Environment, GetOption, Default
from lsst.sconsUtils.utils import libraryLoaderEnvironment
SConscript(os.path.join(".", "bin.src", "SConscript"))

env = Environment(ENV=os.environ)
env["ENV"]["OMP_NUM_THREADS"] = "1"  # Disable threading


def getExecutableCmd(package, script, *args, directory=None):
    """
    Given the name of a package and a script or other executable which lies
    within the given subdirectory (defaults to "bin"), return an appropriate
    string which can be used to set up an appropriate environment and execute
    the command.
    This includes:
    * Specifying an explict list of paths to be searched by the dynamic linker;
    * Specifying a Python executable to be run (we assume the one on the
      default ${PATH} is appropriate);
    * Specifying the complete path to the script.
    """
    if directory is None:
        directory = "bin"
    cmds = [libraryLoaderEnvironment(), "python", os.path.join(env.ProductDir(package), directory, script)]
    cmds.extend(args)
    return " ".join(cmds)


TESTDATA_ROOT = env.ProductDir("testdata_ci_hsc")
PKG_ROOT = env.ProductDir("ci_hsc_gen3")
REPO_ROOT = os.path.join(PKG_ROOT, "DATA_REPO")


run_demo = env.Command(os.path.join(REPO_ROOT, "shared", "ci_hsc_output"), None,
                       ["bin/run_demo.sh"])

env.Alias("all", run_demo)
Default(run_demo)

# env.Clean(everything, [y for x in everything for y in x])
