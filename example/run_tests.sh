#!/usr/bin/env bash

# Simple example of running running a test.
# For simplicity e10s is disabled, ideally we'd have 2 jobs (I think):
#   - e10s disabled
#   - e10s enabled

export AREWESLIMYET=$(dirname $(dirname $0))
export PYTHONPATH=$AREWESLIMYET
export PREFS=${PREFS:-$AREWESLIMYET/example/prefs.json}
export TESTVARS=${TESTVARS:-$AREWESLIMYET/example/testvars.json}
export FIREFOX=${FIREFOX:-/mozilla/builds/nightly/mozilla/firefox-opt/dist/bin/firefox}
export GECKOLOG=${GECKOLOG:-/tmp/gecko.log}

# Note: the example testvars.json just dumps in a temporary directory which
# is written to stdout. Look for processing data in ...! in the
# console output.

#marionette --disable-e10s --preferences "prefs.json" --testvars "testvars.json" \
    marionette \
        --preferences "$PREFS" \
        --testvars "$TESTVARS" \
        --binary "$FIREFOX" \
        --gecko-log "$GECKOLOG" \
        --log-tbpl=- \
	    $AREWESLIMYET/awsylite/test_memory_usage.py

