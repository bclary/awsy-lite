#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


# mozhttpd web server.

import argparse
import os
import socket

import mozhttpd


# directory of this file
here = os.path.dirname(os.path.realpath(__file__))


class WebServers(object):
    def __init__(self, host, port, docroot, count):
        self.host = host
        self.port = port
        self.docroot = docroot
        self.count = count
        self.servers = []

    def start(self):
        self.stop()
        self.servers = []
        port = self.port
        while len(self.servers) < self.count:
            self.servers.append(
                mozhttpd.MozHttpd(host=self.host,
                                  port=port,
                                  docroot=self.docroot))
            try:
                self.servers[-1].start()
            except socket.error, error:
                if isinstance(error, socket.error):
                    if error.errno == 98:
                        print "port %d is in use." % port
                    else:
                        print "port %d error %s" % (port, error)
                elif isinstance(error, str):
                    print "port %d error %s" % (port, error)
                self.servers.pop()
            except Exception, error:
                print "port %d error %s" % (port, error)
                self.servers.pop()

            port += 1

    def stop(self):
        while len(self.servers) > 0:
            server = self.servers.pop()
            server.stop()


def main():
    parser = argparse.ArgumentParser(
        description='Start mozhttpd servers for use by areweslimyet.')

    parser.add_argument('--port', type=int, default=8001,
                        help='Starting port. Defaults to 8001. Web servers will be '
                        'created for each port from the starting port to starting port '
                        '+ count - 1.')
    parser.add_argument('--count', type=int, default=100,
                        help='Number of web servers to start. Defaults to 100.')
    parser.add_argument('--host', type=str, default='localhost',
                        help='Name of webserver host. Defaults to localhost.')

    args = parser.parse_args()
    web_servers = WebServers(args.host, args.port, "%s/html" % here, argc.count)
    web_servers.start()

if __name__ == "__main__":
    main()
