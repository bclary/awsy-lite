#!/usr/bin/env bash

# Simple example of running running a test, tp5 should already be installed.
# For simplicity e10s is disabled, ideally we'd have 2 jobs (I think):
#   - e10s disabled
#   - e10s enabled
mkdir data

# Note: the example testvars.json just dumps the results in "data/", ideally
#       this would be an absolute path to a temp dir.
#marionette --disable-e10s --preferences "prefs.json" --testvars "testvars.json" \
marionette --preferences "prefs.json" --testvars "testvars.json" \
           --binary "firefox/firefox" --gecko-log "data/gecko.log" \
           --log-tbpl=- \
	         ../awsylite/test_memory_usage.py

# Now extract the data we want to submit to perfherder. This just emits a json
# blob in a format that the log parser understands.
../awsylite/process_perf_data.py data/
