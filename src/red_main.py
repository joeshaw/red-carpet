###
### Copyright 2002 Ximian, Inc.
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the GNU General Public License, version 2,
### as published by the Free Software Foundation.
###
### This program is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.
###
### You should have received a copy of the GNU General Public License
### along with this program; if not, write to the Free Software
### Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
###

import sys, os, signal, time, threading
import gtk
import ximian_xmlrpclib
import rcd_util
import red_packagearray
import red_appwindow
import red_channeloption
import red_channelbrowse
import red_summary
import red_search, red_system
import red_transaction
import red_subscriptions
import red_prefs

red_name = "Red Carpet 2: Electric Boogaloo"
red_version = "0.0.1"

gtk.threads_init()

def connect_to_server():
    ## Make contact with the daemon.
    ## We assume local access only
    url = "/var/run/rcd/rcd"
    username = None
    password = None

    transport_debug = os.environ.has_key("RC_TRANSPORT_DEBUG")

    try:
        server = ximian_xmlrpclib.Server(url,
                                         auth_username=username,
                                         auth_password=password,
                                         verbose=transport_debug)
    except:
        sys.stderr.write("Unable to connect to the daemon.\n")
        sys.exit(1)

    rcd_util.register_server(server)

    return server

###
### This is some code to help us track down performance problems
### in GtkTreeView, etc.  Turned off by default.
###

last_tick = time.time()
def tick_cb():
    global last_tick
    now = time.time()
    if now - last_tick > 0.5:
        print "***"
        print "*** UI was blocked for %.2fs" % (now-last_tick)
        print "***"
    last_tick = now
    return 1

class TickThread(threading.Thread):

    def run(self):
        while 1:
            now = time.time()
            if now - last_tick > 2:
                print "UI blocked for %.2fs" % (now-last_tick)
                os.kill(os.getpid(), signal.SIGTRAP)
            time.sleep(1)

def ticker():
    gtk.timeout_add(50, tick_cb);
    TickThread().start()

###
### main
###
   
def main(version):
    server = connect_to_server()

    #ticker()

    app = red_appwindow.AppWindow(server)

    app.register_component(red_summary.SummaryComponent())
    app.register_component(red_subscriptions.SubscriptionsComponent())
    app.register_component(red_channelbrowse.ChannelBrowseComponent())
    app.register_component(red_transaction.TransactionComponent())
    app.register_component(red_system.SystemComponent())
    app.register_component(red_search.SearchComponent())
    app.register_component(red_prefs.PrefsComponent())

    app.set_title(red_name)
    app.set_size_request(780, 550)
    app.show()

    gtk.threads_enter()
    gtk.main()
    gtk.threads_leave()
    


