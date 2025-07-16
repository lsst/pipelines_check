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

"""Check whether output chain was updated."""

import sys

from lsst.daf.butler import Butler, MissingCollectionError


def check_chain(
    butler_uri: str, output_run: str, output_chain: str, should_exist: bool
) -> bool:
    """Check whether output run collextion is in the output chain collection.

    Parameters
    ----------
    butler_uri : `str`
        Butler connection string.
    output_run : `str`
        Output run collection.
    output_chain : `str`
        Output collection (chain).
    should_exist : `bool`
        Whether the output run should exist in the output chain.
    """
    butler = Butler(butler_uri)

    input_collections = {"HSC/calib", "HSC/raw/all", "refcats"}

    try:
        chain_definition = set(butler.registry.getCollectionChain(output_chain))
        exists = output_run in chain_definition
        if should_exist and not exists:
            print(
                f"ERROR: output run ({output_run}) not in output chain ({output_chain}).",
                file=sys.stderr,
            )
        elif not should_exist and exists:
            print(
                f"ERROR: output run ({output_run}) is in output chain ({output_chain}) but shouldn't be.",
                file=sys.stderr,
            )
        exists = input_collections.issubset(chain_definition)
        if should_exist and not exists:
            print(
                f"ERROR: input collections ({input_collections}) not in output chain ({output_chain}).",
                file=sys.stderr,
            )
        elif not should_exist and exists:
            print(
                f"ERROR: input collections ({input_collections}) are in output chain ({output_chain}) "
                " but shouldn't be.",
                file=sys.stderr,
            )
    except MissingCollectionError:
        if should_exist:
            print(
                f"ERROR: output chain did not exist ({output_chain}))", file=sys.stderr
            )
        exists = False

    success = exists == bool(int(should_exist))
    if not success:
        print("ERROR: checking chain failed.", file=sys.stderr)
    return success


if __name__ == "__main__":
    success = check_chain(sys.argv[1], sys.argv[2], sys.argv[3], bool(int(sys.argv[4])))
    sys.exit(not success)  # Exit with 0 if success.
