#!/usr/bin/env python

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

import click
import re
import sys


@click.command
@click.argument("EXPECTED", type=int)
@click.option(
    "--aggregate-graph",
    is_flag=True,
    help="Expect aggregate-graph output instead of transfer-from-graph output.",
)
def check_transfer_count(expected: int, aggregate_graph: bool = False) -> None:
    """Read the number of datasets transferred from the output of
    `butler transfer-from-graph` or `butler aggregate-graph` that has been
    redirected to STDIN.

    The original output is echoed directly as well.
    """
    if aggregate_graph:
        pattern = re.compile(r"Ingested (?P<n>\d+) dataset\(s\)")
    else:
        pattern = re.compile(r"Number of datasets transferred: (?P<n>\d+)")
    found = False
    for line in sys.stdin:
        print(line)
        if m := pattern.search(line):
            n = int(m.group("n"))
            if n != expected:
                raise ValueError(f"{n} datasets transferred; expected {expected}.")
            else:
                found = True
    if not found:
        raise ValueError("Transferred dataset count not found in output.")


if __name__ == "__main__":
    check_transfer_count()
