# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import os
import shutil
import socket
import sys
import tempfile
import time
import urllib
import zipfile

from marionette_harness import MarionetteTestCase
from marionette_driver import Actions
from marionette_driver.errors import JavascriptException, ScriptTimeoutException
import mozlog.structured
from marionette_driver.keys import Keys

import mozfile

from awsylite import *


class TestMemoryUsage(MarionetteTestCase):
    """Provides a test that collects memory usage at various checkpoints:
      - "Start" - Just after startup
      - "StartSettled" - After an additional wait time
      - "TabsOpen" - After opening all provided URLs
      - "TabsOpenSettled" - After an additional wait time
      - "TabsOpenForceGC" - After forcibly invoking garbage collection
      - "TabsClosed" - After closing all tabs
      - "TabsClosedSettled" - After an additional wait time
      - "TabsClosedForceGC" - After forcibly invoking garbage collection
    """

    def _install_tp5(self, url="https://people-mozilla.org/~jmaher/taloszips/zips/tp5n.zip"):
        # XXX: bc: Need to handle the following cases:
        # 1. download and install tp5 from people
        # 2. download and install tp5 from tooltool
        # 3. use existing tp5
        # from in automation, get it from tooltool
        # http://searchfox.org/mozilla-central/source/testing/mozharness/mozharness/mozilla/testing/talos.py#336
        # http://searchfox.org/mozilla-central/source/testing/talos/tp5n-pageset.manifest

        html_dir = tempfile.mkdtemp()
        tp5nzip_path = os.path.join(html_dir, "tp5n.zip")
        (path, httplib_httpmessage) = urllib.urlretrieve(url, tp5nzip_path)
        tp5n_path = os.path.join(html_dir, "tp5n")
        tp5_path = os.path.join(html_dir, "tp5")
        files = mozfile.extract_zip(tp5nzip_path, html_dir)
        shutil.move(tp5n_path, tp5_path)

        return html_dir

    def setUp(self):
        MarionetteTestCase.setUp(self)
        self.logger = mozlog.structured.structuredlog.get_default_logger()
        self.logger.info("setting up!")

        self.marionette.set_context('chrome')

        self._html_dir = self._install_tp5()
        self._webservers = webservers.WebServers("localhost", 8001, self._html_dir, 100)
        self._webservers.start()
        test_sites = []
        i = 0
        for server in self._webservers.servers:
            test_sites.append(TEST_SITES_TEMPLATES[i].format(server.port))
            i += 1
        self._urls = self.testvars.get("urls", test_sites)
        self._pages_to_load = self.testvars.get("entities", len(self._urls))
        self._iterations = self.testvars.get("iterations", ITERATIONS)
        self._perTabPause = self.testvars.get("perTabPause", PER_TAB_PAUSE)
        self._settleWaitTime = self.testvars.get(
            "settleWaitTime", SETTLE_WAIT_TIME)
        self._maxTabs = self.testvars.get("maxTabs", MAX_TABS)
        self._resultsDir = tempfile.mkdtemp()

        self.reset_state()
        self.logger.info("done setting up!")

    def tearDown(self):
        self.logger.info("tearing down!")
        MarionetteTestCase.tearDown(self)
        self.logger.info("tearing down webservers!")
        # Be a little paranoid about making sure _html_dir was
        # initialized before removing the tree!
        if hasattr(self, '_html_dir') and self._html_dir:
            shutil.rmtree(self._html_dir)
        self._webservers.stop()
        self.logger.info("processing data in %s!" % self._resultsDir)
        perf_blob = process_perf_data.create_perf_data(self._resultsDir)
        print "PERFHERDER_DATA: %s" % json.dumps(perf_blob)
        self.logger.info("done tearing down!")

    def reset_state(self):
        self._pages_loaded = 0

        # Close all tabs except one
        for x in range(len(self.marionette.window_handles) - 1):
            self.logger.info("closing window")
            self.marionette.execute_script("gBrowser.removeCurrentTab();")
            time.sleep(0.25)

        self._tabs = self.marionette.window_handles
        self.marionette.switch_to_window(self._tabs[0])

    def do_full_gc(self):
        """Performs a full garbage collection cycle and returns when it is finished.

        Returns True on success and False on failure.
        """
        # NB: we could do this w/ a signal or the fifo queue too
        self.logger.info("starting gc...")
        gc_script = """
            const Cu = Components.utils;
            const Cc = Components.classes;
            const Ci = Components.interfaces;

            Cu.import("resource://gre/modules/Services.jsm");
            Services.obs.notifyObservers(null, "child-mmu-request", null);

            let memMgrSvc = Cc["@mozilla.org/memory-reporter-manager;1"].getService(Ci.nsIMemoryReporterManager);
            memMgrSvc.minimizeMemoryUsage(() => marionetteScriptFinished("gc done!"));
            """
        result = None
        try:
            result = self.marionette.execute_async_script(
                gc_script, script_timeout=180000)
        except JavascriptException, e:
            self.logger.error("GC JavaScript error: %s" % e)
        except ScriptTimeoutException:
            self.logger.error("GC timed out")
        except:
            self.logger.error("Unexpected error: %s" % sys.exc_info()[0])
        else:
            self.logger.info(result)

        return result is not None

    def do_memory_report(self, checkpointName, iteration):
        """Creates a memory report for all processes and and returns the
        checkpoint.

        This will block until all reports are retrieved or a timeout occurs.
        Returns the checkpoint or None on error.

        :param checkpointName: The name of the checkpoint.
        """
        self.logger.info("starting checkpoint %s..." % checkpointName)

        checkpoint_file = "memory-report-%s-%d.json.gz" % (checkpointName, iteration)
        checkpoint_path = os.path.join(self._resultsDir, checkpoint_file)

        checkpoint_script = """
            const Cc = Components.classes;
            const Ci = Components.interfaces;

            let dumper = Cc["@mozilla.org/memory-info-dumper;1"].getService(Ci.nsIMemoryInfoDumper);
            dumper.dumpMemoryReportsToNamedFile(
                "%s",
                () => marionetteScriptFinished("memory report done!"),
                null,
                /* anonymize */ false);
            """ % checkpoint_path

        checkpoint = None
        try:
            finished = self.marionette.execute_async_script(
                checkpoint_script, script_timeout=60000)
            if finished:
              checkpoint = checkpoint_path
        except JavascriptException, e:
            self.logger.error("Checkpoint JavaScript error: %s" % e)
        except ScriptTimeoutException:
            self.logger.error("Memory report timed out")
        except:
            self.logger.error("Unexpected error: %s" % sys.exc_info()[0])
        else:
            self.logger.info("checkpoint created!")

        return checkpoint

    def open_and_focus(self):
        """Opens the next URL in the list and focuses on the tab it is opened in.

        A new tab will be opened if |_maxTabs| has not been exceeded, otherwise
        the URL will be loaded in the next tab.
        """
        page_to_load = self._urls[self._pages_loaded % len(self._urls)]
        tabs_loaded = len(self._tabs)
        is_new_tab = False

        if tabs_loaded < self._maxTabs and tabs_loaded <= self._pages_loaded:
            full_tab_list = self.marionette.window_handles

            # Trigger opening a new tab by finding the new tab button and
            # clicking it
            newtab_button = (self.marionette.find_element('id', 'tabbrowser-tabs')
                                            .find_element('anon attribute',
                                                          {'anonid': 'tabs-newtab-button'}))
            newtab_button.click()

            self.wait_for_condition(lambda mn: len(
                mn.window_handles) == tabs_loaded + 1)

            # NB: The tab list isn't sorted, so we do a set diff to determine
            #     which is the new tab
            new_tab_list = self.marionette.window_handles
            new_tabs = list(set(new_tab_list) - set(full_tab_list))

            self._tabs.append(new_tabs[0])
            tabs_loaded += 1

            is_new_tab = True

        tab_idx = self._pages_loaded % self._maxTabs

        tab = self._tabs[tab_idx]

        # Tell marionette which tab we're on
        # NB: As a work-around for an e10s marionette bug, only select the tab
        #     if we're really switching tabs.
        if tabs_loaded > 1:
            self.logger.info("switching to tab")
            self.marionette.switch_to_window(tab)
            self.logger.info("switched to tab")

        with self.marionette.using_context('content'):
            self.logger.info("loading %s" % page_to_load)
            self.marionette.navigate(page_to_load)
            self.logger.info("loaded!")

        # On e10s the tab handle can change after actually loading content
        if is_new_tab:
            # First build a set up w/o the current tab
            old_tabs = set(self._tabs)
            old_tabs.remove(tab)
            # Perform a set diff to get the (possibly) new handle
            [new_tab] = set(self.marionette.window_handles) - old_tabs
            # Update the tab list at the current index to preserve the tab
            # ordering
            self._tabs[tab_idx] = new_tab

        # give the page time to settle
        time.sleep(self._perTabPause)

        self._pages_loaded += 1

    def signal_user_active(self):
        """Signal to the browser that the user is active.

        Normally when being driven by marionette the browser thinks the
        user is inactive the whole time because user activity is
        detected by looking at key and mouse events.

        This would be a problem for this test because user inactivity is
        used to schedule some GCs (in particular shrinking GCs), so it
        would make this unrepresentative of real use.

        Instead we manually cause some inconsequential activity (a press
        and release of the shift key) to make the browser think the user
        is active.  Then when we sleep to allow things to settle the
        browser will see the user as becoming inactive and trigger
        appropriate GCs, as would have happened in real use.
        """
        action = Actions(self.marionette)
        action.key_down(Keys.SHIFT)
        action.key_up(Keys.SHIFT)
        action.perform()

    def test_open_tabs(self):
        """Marionette test entry that returns an array of checkoint arrays.

        This will generate a set of checkpoints for each iteration requested.
        Upon succesful completion the results will be stored in
        |self.testvars["results"]| and accessible to the test runner via the
        |testvars| object it passed in.
        """
        # setup the results array
        results = [[] for x in range(self._iterations)]

        def create_checkpoint(name, iteration):
            checkpoint = self.do_memory_report(name, iteration)
            self.assertIsNotNone(checkpoint, "Checkpoint was recorded")
            results[iteration].append(checkpoint)

        # The first iteration gets Start and StartSettled entries before
        # opening tabs
        create_checkpoint("Start", 0)
        time.sleep(self._settleWaitTime)
        create_checkpoint("StartSettled", 0)

        for itr in range(self._iterations):
            for x in range(self._pages_to_load):
                self.open_and_focus()
                self.signal_user_active()

            create_checkpoint("TabsOpen", itr)
            time.sleep(self._settleWaitTime)
            create_checkpoint("TabsOpenSettled", itr)
            self.assertTrue(self.do_full_gc())
            create_checkpoint("TabsOpenForceGC", itr)

            # Close all tabs
            self.reset_state()

            self.logger.info("switching to first window")
            self.marionette.switch_to_window(self._tabs[0])
            self.logger.info("switched to first window")
            with self.marionette.using_context('content'):
                self.logger.info("navigating to about:blank")
                self.marionette.navigate("about:blank")
                self.logger.info("navigated to about:blank")
            self.signal_user_active()

            create_checkpoint("TabsClosed", itr)
            time.sleep(self._settleWaitTime)
            create_checkpoint("TabsClosedSettled", itr)
            self.assertTrue(self.do_full_gc(), "GC ran")
            create_checkpoint("TabsClosedForceGC", itr)

        # TODO(ER): Temporary hack until bug 1121139 lands
        self.logger.info("setting results")
        self.testvars["results"] = results
