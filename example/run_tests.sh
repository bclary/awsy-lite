#!/usr/bin/env bash

# Simple example of running running a test, tp5 should already be installed.
# For simplicity e10s is disabled, ideally we'd have 2 jobs (I think):
#   - e10s disabled
#   - e10s enabled
mkdir data

# Note: the example testvars.json just dumps the results in "data/", ideally
#       this would be an absolute path to a temp dir.
marionette --disable-e10s --preferences "prefs.json" --testvars "testvars.json" \
           --binary "../firefox/firefox" --gecko-log "data/gecko.log" \
	   ../awsylite/test_memory_usage.py

# Now extract the data we want to submit to perfherder. Ideally this would just
# be called by a python script that knows how to format the perf blob.

# RSS
echo "resident"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-Start-0.json.gz" "resident"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-StartSettled-0.json.gz" "resident"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsOpen-4.json.gz" "resident"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsOpenSettled-4.json.gz" "resident"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsOpenForceGC-4.json.gz" "resident"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsClosed-4.json.gz" "resident"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsClosedSettled-4.json.gz" "resident"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsClosedForceGC-4.json.gz" "resident"

# explicit
echo "explicit"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-Start-0.json.gz" "explicit/"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-StartSettled-0.json.gz" "explicit/"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsOpen-4.json.gz" "explicit/"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsOpenSettled-4.json.gz" "explicit/"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsOpenForceGC-4.json.gz" "explicit/"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsClosed-4.json.gz" "explicit/"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsClosedSettled-4.json.gz" "explicit/"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsClosedForceGC-4.json.gz" "explicit/"

# heap-unclassified
echo "heap-unclassified"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-Start-0.json.gz" "explicit/heap-unclassified"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-StartSettled-0.json.gz" "explicit/heap-unclassified"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsOpen-4.json.gz" "explicit/heap-unclassified"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsOpenSettled-4.json.gz" "explicit/heap-unclassified"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsOpenForceGC-4.json.gz" "explicit/heap-unclassified"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsClosed-4.json.gz" "explicit/heap-unclassified"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsClosedSettled-4.json.gz" "explicit/heap-unclassified"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsClosedForceGC-4.json.gz" "explicit/heap-unclassified"

# js-main-runtime
echo "js-main-runtime"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-Start-0.json.gz" "js-main-runtime"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-StartSettled-0.json.gz" "js-main-runtime"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsOpen-4.json.gz" "js-main-runtime"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsOpenSettled-4.json.gz" "js-main-runtime"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsOpenForceGC-4.json.gz" "js-main-runtime"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsClosed-4.json.gz" "js-main-runtime"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsClosedSettled-4.json.gz" "js-main-runtime"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsClosedForceGC-4.json.gz" "js-main-runtime"


# images
echo "images"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-Start-0.json.gz" "explicit/images"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-StartSettled-0.json.gz" "explicit/images"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsOpen-4.json.gz" "explicit/images"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsOpenSettled-4.json.gz" "explicit/images"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsOpenForceGC-4.json.gz" "explicit/images"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsClosed-4.json.gz" "explicit/images"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsClosedSettled-4.json.gz" "explicit/images"
../awsylite/parse_about_memory.py --proc-filter="Main" "data/memory-report-TabsClosedForceGC-4.json.gz" "explicit/images"

# All the stuff in "data" would be uploaded as an artifact to S3.
# Treeherder job would then be submitted with perf blob.
