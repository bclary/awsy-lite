#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import math
import os
import parse_about_memory
import sys

# A description of each checkpoint and the root path to it.
CHECKPOINTS = [
    { 'name': "Fresh start", 'path': "memory-report-Start-0.json.gz" },
    { 'name': "Fresh start [+30s]", 'path': "memory-report-StartSettled-0.json.gz" },
    { 'name': "After tabs open", 'path': "memory-report-TabsOpen-4.json.gz" },
    { 'name': "After tabs open [+30s]", 'path': "memory-report-TabsOpenSettled-4.json.gz" },
    { 'name': "After tabs open [+30s, forced GC]", 'path': "memory-report-TabsOpenForceGC-4.json.gz" },
    { 'name': "Tabs closed", 'path': "memory-report-TabsClosed-4.json.gz" },
    { 'name': "Tabs closed [+30s]", 'path': "memory-report-TabsClosedSettled-4.json.gz" },
    { 'name': "Tabs closed [+30s, forced GC]", 'path': "memory-report-TabsClosedForceGC-4.json.gz" }
]

# A description of each perfherder suite and the path to its values.
PERF_SUITES = [
    { 'name': "Resident Memory", 'node': "resident" },
    { 'name': "Explicit Memory", 'node': "explicit/" },
    { 'name': "Heap Unclassified", 'node': "explicit/heap-unclassified" },
    { 'name': "JS", 'node': "js-main-runtime" },
    { 'name': "Images", 'node': "explicit/images" }
]


def create_suite(name, node, data_path):
    """
    Creates a suite suitable for adding to a perfherder blob. Calculates the
    geometric mean of the checkpoint values and adds that to the suite as
    well.

    :param name: The name of the suite.
    :param node: The path of the data node to extract data from.
    :param data_path: The directory to retrieve data from.
    """
    suite = {
        'name': name,
        'subtests': [],
        'lowerIsBetter': True,
        'units': 'bytes'
    }

    total = 0
    for checkpoint in CHECKPOINTS:
        memory_report_path = os.path.join(data_path, checkpoint['path'])

        # Currently limited to just the main process.
        totals = parse_about_memory.calculate_memory_report_values(
                                        memory_report_path, node, 'Main')
        # For e10s we would sum the values, except for rss which we'd want
        # rss of main + uss of not main.
        value = totals.values()[0]

        subtest = {
            'name': checkpoint['name'],
            'value': value,
            'lowerIsBetter': True,
            'units': 'bytes'
        }
        suite['subtests'].append(subtest);
        total += math.log(subtest['value'])

    # Add the geometric mean. For more details on the calculation see:
    #   https://en.wikipedia.org/wiki/Geometric_mean#Relationship_with_arithmetic_mean_of_logarithms
    suite['value'] = math.exp(total / len(CHECKPOINTS))

    return suite


def create_perf_data(data_path):
    """
    Builds up a performance data blob suitable for submitting to perfherder.
    """
    perf_blob = {
        'framework': { 'name': 'awsy' },
        'suites': []
    }

    for suite in PERF_SUITES:
        perf_blob['suites'].append(create_suite(suite['name'], suite['node'], data_path))

    return perf_blob


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print "Usage: process_perf_data.py data_path"
        sys.exit(1)

    # Determine which revisions we need to process.
    data_path = args[0]
    perf_blob = create_perf_data(data_path)
    print "PERFHERDER_DATA: %s" % json.dumps(perf_blob)

    sys.exit(0)
