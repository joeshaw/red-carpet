###
### Copyright (C) 2002-2003 Ximian, Inc.
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

import os, time, threading, gtk

red_name      = "Red Carpet"
red_version   = None
red_copyright = "2002-2003"
debug         = os.getenv("RC_GUI_DEBUG")

from red_gettext import _
import rcd_util
import red_console
import red_appwindow
import red_search
import red_summary
import red_transaction
import red_news
import red_history


red_running = 1

gtk.threads_init()

###
### This is some code to help us track down performance problems
### in GtkTreeView, etc.  Turned off by default.
###

last_tick = time.time()
def tick_cb():
    global last_tick
    last_tick = time.time()
    return 1

class TickThread(threading.Thread):

    def run(self):
        self.last_tick = last_tick
        self.last_block = 0
        while red_running:
            now = time.time()
            if now - last_tick > 0.25:
                if self.last_block == 0:
                    print "**** UI is blocking!"
                    #os.kill(os.getpid(), signal.SIGTRAP)
                self.last_block = now
                self.last_tick = last_tick
            else:
                if self.last_block:
                    t = self.last_block - self.last_tick
                    print "**** UI blocked for approx %.2fs" % t
                self.last_block = 0
                #os.kill(os.getpid(), signal.SIGTRAP)
            time.sleep(0.1)

def ticker():
    gtk.timeout_add(50, tick_cb);
    TickThread().start()

###
### main
###
   
def main(version):
    global red_version
    red_version = version
    
    print "Red Carpet Client %s" % version
    print "Copyright (C) 2002-2003 Ximian Inc."
    print

    server = rcd_util.get_server()

    if debug:
        ticker()

    app = red_appwindow.AppWindow(server)
    app.set_title(red_name + " " + red_version)

    app.register_component(red_summary.SummaryComponent())
    app.register_component(red_search.SearchComponent())
    app.register_component(red_news.NewsComponent())
    app.register_component(red_transaction.TransactionComponent())
    app.register_component(red_history.HistoryComponent())

    app.set_size_request(780, 550)
    app.show()

    gtk.threads_enter()

    gtk.main()

    global red_running
    red_running = 0
    
    gtk.threads_leave()
    


