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
import rcd_util
import red_main

class PendingView(gtk.Window):

    def __init__(self, title=None, label=None,
                 parent=None,
                 timeout_len=400, show_rate=1, show_size=1, is_modal=1):
        gtk.Window.__init__(self, gtk.WINDOW_POPUP)

        self.set_resizable(0)

        self.set_modal(is_modal)

        if parent:
            self.set_transient_for(parent)
            self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        else:
            self.set_position(gtk.WIN_POS_CENTER)

        self.pending_list = []
        self.polling_timeout = 0
        self.finished_lag = 600

        self.timeout_len = timeout_len
        self.show_rate = show_rate
        self.show_size = show_size

        self.ourframe = gtk.Frame()
        self.add(self.ourframe)

        self.mainbox = gtk.VBox(0, 10)
        self.mainbox.set_border_width(10)
        self.ourframe.add(self.mainbox)

        self.title_label = gtk.Label("")
        self.title_label.set_alignment(0, 0.5)
        if title:
            self.title_label.set_markup("<b><big>%s</big></b>" % title)
        self.mainbox.pack_start(self.title_label, 0, 0, 0)

        self.step_label = gtk.Label("")
        self.step_label.set_alignment(0, 0.5)
        self.mainbox.pack_start(self.step_label, 0, 0, 0)
        if label:
            self.step_label.set_text(label)

        self.progress_bar = gtk.ProgressBar()
        self.mainbox.pack_start(self.progress_bar, 0, 0, 0)

        self.ourframe.show_all()
        

    def start_timeout(self):
        if self.polling_timeout:
            return

        self.polling_timeout = gtk.timeout_add(self.timeout_len,
                                               self.poll)

    def stop_timeout(self):
        if not self.polling_timeout:
            return

        gtk.timeout_remove(self.polling_timeout)
        self.polling_timeout = 0

    def set_pending_list(self, list):
        self.pending_list = list
        if list:
            self.start_timeout()
        
    def update(self, percent,
               elapsed_sec, remaining_sec,
               completed_size, total_size):

        if percent <= 0:
            self.progress_bar.set_text("")
            self.progress_bar.pulse()
        else:
            rate = 0
            if elapsed_sec > 0:
                rate = completed_size / elapsed_sec

            self.progress_bar.set_fraction(percent / 100.0)

            msg = "%.1f%%" % percent

            if self.show_rate and total_size > 0 and rate > 0:
                rate_str = rcd_util.byte_size_to_string(rate) + "/s"
            else:
                rate_str = None

            if self.show_size and total_size > 0:
                cs = rcd_util.byte_size_to_string(completed_size)
                ts = rcd_util.byte_size_to_string(total_size)
                msg = msg + " - %s / %s" % (cs, ts)
                if rate_str:
                    msg = msg + " (" + rate_str + ")"
            else:
                if rate_str:
                    msg = msg + " - " + rate_str

            self.progress_bar.set_text(msg)


    def poll(self):

        polling = 0
        
        rate = 0
        percent = 0
        elapsed_sec = 0
        remaining_sec = 0
        completed_size = 0
        total_size = 0

        for tid in self.pending_list:
            server = rcd_util.get_server()
            pending = server.rcd.system.poll_pending(tid)

            if pending["is_active"]:
                percent = percent + pending["percent_complete"]
                polling = 1
            else:
                percent = percent + 100

            elapsed_sec = max(elapsed_sec,
                              pending.get("elapsed_sec", 0))
            remaining_sec = max(remaining_sec,
                                pending.get("remaining_sec", 0))

            completed_size = completed_size + \
                             pending.get("completed_size", 0)
            total_size = total_size + \
                         pending.get("total_size", 0)

        if self.pending_list:
            percent = percent / len(self.pending_list)
            self.update(percent, elapsed_sec, remaining_sec,
                        completed_size, total_size)

        if not polling:
            def finished_cb(x):
                x.destroy()
                return 0
            gtk.timeout_add(self.finished_lag, finished_cb, self)
            self.polling_timeout = 0
            return 0
        
        return 1

