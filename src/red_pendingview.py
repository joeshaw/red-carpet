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

import string
import gobject, gtk

class PendingView(gtk.VBox):

    def __init__(self):
        gobject.GObject.__init__(self)

        self.have_server = 0
        self.server = None
        self.pending_list = []
        self.polling_timeout = 0

        # Assemble our widgets 
        self.progress = gtk.ProgressBar()
        self.message = gtk.Label("")

        self.pack_start(self.progress, 1, 1, 4)
        self.pack_start(self.message,  1, 1, 4)

        self.progress.show()
        self.message.show()

    def start_timeout(self):
        if self.polling_timeout:
            return
        if self.have_server and self.pending_list:
            self.polling_timeout = gtk.timeout_add(400, PendingView.poll, self)

    def set_server(self, serv):
        self.have_server = 1
        self.server = serv
        self.start_timeout()

    def set_pending_list(self, list):
        self.pending_list = list
        self.start_timeout()
        
    # FIXME: ugly as sin
    def update(self, percent,
               elapsed_sec, remaining_sec,
               completed_size, total_size):

        rate = 0
        if elapsed_sec > 0:
            rate = completed_size / elapsed_sec
        
        self.progress.set_fraction(percent / 100.0)
        self.progress.set_text("%d of %d" % (completed_size, total_size))

        msg = "rate %.1f, %ds elapsed, %ds remaining" % \
              (rate, elapsed_sec, remaining_sec)
        self.message.set_text(msg)

        while gtk.events_pending():
            gtk.main_iteration()


    def poll(self):

        polling = 0
        
        rate = 0
        percent = 0
        elapsed_sec = 0
        remaining_sec = 0
        completed_size = 0
        total_size = 0

        for tid in self.pending_list:
            pending = self.server.rcd.system.poll_pending(tid)

            if pending["is_active"]:
                percent = percent + pending["percent_complete"]
                elapsed_sec = max(elapsed_sec,
                                  pending.get("elapsed_sec", 0))
                remaining_sec = max(remaining_sec,
                                    pending.get("remaining_sec", 0))
                polling = 1
            else:
                percent = percent + 100

            completed_size = completed_size + \
                             pending.get("completed_size", 0)
            total_size = total_size + \
                         pending.get("total_size", 0)

        percent = percent / len(self.pending_list)

        self.update(percent, elapsed_sec, remaining_sec,
                    completed_size, total_size)

        # If we are finished, we emit our signal and return false so that
        #  the timeout goes away.
        if not polling:
            self.polling_timeout = 0
            self.emit("finished")
        
        return polling



gobject.type_register(PendingView)

gobject.signal_new("finished",
                   PendingView,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   ())
