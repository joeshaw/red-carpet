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

import red_extra
import os, signal
import sys, string, threading, gobject, gtk, pango
import ximian_xmlrpclib
import rcd_util
import red_pendingops, red_serverlistener
import red_pixbuf

from red_gettext import _

MAX_LABEL_LEN = 20
WRAP_LABEL_LEN = 40

# We don't really have any idea how long the transaction will take, but
# we'll guess that the download is 2/3 and the actual transaction 1/3.
DOWNLOAD_MULTIPLIER = .667

class PendingView(gtk.Window):

    def __init__(self, title=None, label=None,
                 parent=None,
                 timeout_len=200, show_rate=1, show_size=1, is_modal=1,
                 allow_cancel=0,
                 self_destruct=0,
                 total_progress_bar=0):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

        self.set_modal(is_modal)

        self.window_parent = parent
        if parent:
            self.set_transient_for(parent)
        self.position_window()

        self.icons = None
        self.curr_icon = 0
        self.icon_timeout = 0

        self.pending_list = []
        self.polling_timeout = 0
        self.finished_lag = 600

        self.timeout_len = timeout_len
        self.show_rate = show_rate
        self.show_size = show_size
        self.self_destruct = self_destruct
        self.allow_cancel = allow_cancel
        self.cancel_button = 0

        self.ourframe = gtk.Frame()
        self.add(self.ourframe)

        mainbox = gtk.VBox(0, 10)
        mainbox.set_border_width(10)
        self.ourframe.add(mainbox)

        topbox = gtk.HBox(0, 0)
        self.image = gtk.Image()
        topbox.pack_start(self.image, expand=0, fill=1, padding=5)

        textbox = gtk.VBox(0, 0)
        topbox.pack_end(textbox, expand=1, fill=1)

        mainbox.pack_start(topbox, expand=1, fill=1)

        self.title_label = gtk.Label("")
        self.title_label.set_alignment(0, 0.5)
        textbox.pack_start(self.title_label, expand=0, fill=0)

        self.step_label = gtk.Label("")
        self.step_label.set_alignment(0, 0.0)
        (width, height) = self.calculate_required_text_size(MAX_LABEL_LEN)
        self.step_label.set_size_request(width, -1)
        self.__line_height = height

        viewport = gtk.Viewport()
        viewport.set_shadow_type(gtk.SHADOW_NONE)
        viewport.add(self.step_label)

        scrolled = gtk.ScrolledWindow()
        scrolled.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scrolled.set_shadow_type(gtk.SHADOW_IN)
        scrolled.set_size_request(-1, 3*height+2) # a few extra pixels...
        scrolled.add(viewport)
        self.__scrolled = scrolled
        textbox.pack_start(scrolled, expand=1, fill=1)
        
        if label:
            self.set_label(label)

        self.window_title = title
        self.set_title(self.window_title)

        self.progress_bar = gtk.ProgressBar()
        mainbox.pack_start(self.progress_bar, expand=0, fill=0)

        if total_progress_bar:
            self.total_progress_bar = gtk.ProgressBar()
            mainbox.pack_start(self.total_progress_bar, expand=0, fill=0)

            self.update_total(0)

        self.button = None
        if self.allow_cancel or not self.self_destruct:
            bbox = gtk.HButtonBox()
            bbox.set_layout(gtk.BUTTONBOX_END)
            mainbox.pack_end(bbox, 0, 0, 0)
            if self.allow_cancel:
                self.button = gtk.Button(gtk.STOCK_CANCEL)
                self.cancel_button = 1
            else:
                self.button = gtk.Button(gtk.STOCK_OK)
                self.button.set_sensitive(0)
            self.button.set_use_stock(1)
            bbox.pack_start(self.button, 0, 0, 0)
            self.button.set_flags(gtk.CAN_DEFAULT)
            self.button.grab_default()

            def button_handler_cb(b, pv):
                if pv.cancel_button:
                    pv.cancelled()
                else:
                    pv.destroy()
            self.button.connect("clicked", button_handler_cb, self)

        def delete_event_cb(self, x):
            if self.button and self.button.get_property("sensitive"):
                self.button.emit("clicked")
            return 1

        self.connect("delete_event", delete_event_cb)

        self.ourframe.show_all()

    def set_icons(self, icons, interval=300):
        if self.icon_timeout:
            gtk.timeout_remove(self.icon_timeout)
            self.icon_timeout = 0
            
        self.icons = []
        for x in icons:
            pixbuf = red_pixbuf.get_pixbuf(x)
            if pixbuf:
                self.icons.append(pixbuf)
        if self.icons:
            self.image.set_from_pixbuf(self.icons[0])

        if len(self.icons) > 1:
            def icon_cb(pv):
                pv.curr_icon += 1
                if pv.curr_icon >= len(pv.icons):
                    pv.curr_icon = 0
                pv.image.set_from_pixbuf(pv.icons[pv.curr_icon])
                return 1

            self.icon_timeout = gtk.timeout_add(interval,
                                                icon_cb,
                                                self)

    def set_icon(self, icon):
        self.set_icons((icon, ))

    def stop_icon_anim(self):
        if self.icon_timeout:
            gtk.timeout_remove(self.icon_timeout)
            self.icon_timeout = 0
            if self.icons:
                self.image.set_from_pixbuf(self.icons[0])

    def position_window(self):
        if self.window_parent:
            self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        else:
            self.set_position(gtk.WIN_POS_CENTER)

    def calculate_required_text_size(self, max_len):
        # "W" being the widest glyph.
        s = "W"*max_len
        layout = pango.Layout(gtk.Label("").get_pango_context())
        layout.set_text(s)
        (width, height) = layout.get_pixel_size()

        return (width, height)

    def disable_cancellation(self):
        if self.allow_cancel:
            self.button.set_sensitive(0)

    def cancelled(self):
        self.stop_icon_anim()

    def finished(self):
        self.stop_icon_anim()
        self.emit("finished")

    def set_title(self, msg):
        ## Guard for None
        msg = msg or ""
        gtk.Window.set_title(self, msg)
        self.title_label.set_markup("<b><big>%s</big></b>" % (msg or ""))
        self.position_window() # keep window centered

    def set_label(self, msg):
        if msg:
            lines = rcd_util.linebreak(msg, WRAP_LABEL_LEN)
        else:
            lines = []

        # Try to set the scrollbox to a reasonable size, neither too big
        # or too small. (We always want at least 3 lines of text to avoid
        # "jumpyness".)
        n = max(3, min(len(lines), 8))
        self.__scrolled.set_size_request(-1, n*self.__line_height+2)

        msg = string.join(lines, "\n")
        self.step_label.set_text(msg)
        self.position_window() # keep window centered

    def start_polling(self):
        if self.polling_timeout:
            return

        self.polling_timeout = gtk.timeout_add(self.timeout_len,
                                               self.poll)

    def stop_polling(self):
        if not self.polling_timeout:
            return

        gtk.timeout_remove(self.polling_timeout)
        self.polling_timeout = 0

    def update_pulse(self):
        self.progress_bar.set_text("")
        self.progress_bar.pulse()

    def update_fill(self):
        self.progress_bar.set_fraction(1.0)
        self.progress_bar.set_text("")

    def update(self, percent,
               elapsed_sec, remaining_sec,
               completed_size, total_size,
               show_size=1, show_rate=1):

        if percent <= 0:
            self.update_pulse()
        else:
            rate = 0
            if elapsed_sec > 0:
                rate = completed_size / elapsed_sec

            self.progress_bar.set_fraction(percent / 100.0)

            msg = "%.1f%%" % percent

            if show_rate and rate > 0:
                rate_str = rcd_util.byte_size_to_string(rate) + "/s"
            else:
                rate_str = None

            if show_size and total_size > 0:
                cs = rcd_util.byte_size_to_string(completed_size)
                if total_size > 0:
                    ts = rcd_util.byte_size_to_string(total_size)
                    msg = msg + " - %s / %s" % (cs, ts)
                else:
                    msg = msg + " - %s" % cs
                if rate_str:
                    msg = msg + " (" + rate_str + ")"
            else:
                if rate_str:
                    msg = msg + " - " + rate_str

            self.progress_bar.set_text(msg)

        # If our window has grown our shrunk, we want to make sure
        # that it stays centered.
        self.position_window()


    def update_from_pendings(self, pending_list,
                             show_size=1, show_rate=1):

        rate = 0
        percent = 0
        elapsed_sec = 0
        remaining_sec = 0
        completed_size = 0
        total_size = 0
        know_total_size = 1

        for pending in pending_list:
            if pending["is_active"]:
                percent = percent + pending["percent_complete"]
            else:
                percent = percent + 100

            elapsed_sec = max(elapsed_sec, pending.get("elapsed_sec", 0))
            remaining_sec = max(remaining_sec, pending.get("remaining_sec", 0))

            completed_size = completed_size + pending.get("completed_size", 0)
            ts = pending.get("total_size", 0)
            if ts <= 0:
                know_total_size = 0
            total_size = total_size + ts

        if not know_total_size:
            total_size = -1

        if pending_list:
            percent = percent / len(pending_list)
            self.update(percent, elapsed_sec, remaining_sec,
                        completed_size, total_size,
                        show_size=show_size, show_rate=show_rate)

            return (percent, elapsed_sec, remaining_sec,
                    completed_size, total_size)
        else:
            return (-1, -1, -1, -1, -1)


    def update_from_pending(self, pending, show_size=1, show_rate=1):
        return self.update_from_pendings([pending],
                                         show_size=show_size,
                                         show_rate=show_rate)

    def update_total(self, percent):
        self.total_progress_bar.set_fraction(percent / 100.0)
        self.total_progress_bar.set_text(_("%.1f%% completed") % percent)

    # Define me!
    def poll_worker(self):
        assert 0

    def switch_cancel_button_to_ok(self):
        if self.cancel_button:
            self.button.set_label(gtk.STOCK_OK)
            self.cancel_button = 0

    def poll(self):
        polling = self.poll_worker()

        if not polling:
            def finished_cb(x):
                if x.self_destruct:
                    x.finished()
                    x.destroy()
                else:
                    # If necessary, change the button from "Cancel"
                    # to "OK".  Make sure the button sensitive.
                    if x.button:
                        x.switch_cancel_button_to_ok()
                        x.button.set_sensitive(1)
                return 0
            gtk.timeout_add(self.finished_lag, finished_cb, self)
            self.polling_timeout = 0
            self.pending_list = []
            return 0
        
        return 1


#gobject.type_register(PendingView)

gobject.signal_new("finished",
                   PendingView,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   ())


##############################################################################

class PendingView_Simple(PendingView):

    def __init__(self, title, parent=None):
        PendingView.__init__(self, title, parent=parent,
                             self_destruct=1, allow_cancel=0,
                             timeout_len=150)

        self.pending_list = []

        self.max_threads = 5

        self.pending_countdown = 0
        self.poll_queue = []
        self.poll_results = {}
        self.finished_polling = 0

    def set_pending_list(self, pending_list):
        self.pending_list = pending_list

        if self.pending_list:
            self.start_polling()
            red_serverlistener.freeze_polling()
        else:
            self.finished()
            self.destroy()

    def launch_poll_threads(self, launch_max=0):
        server = rcd_util.get_server_proxy()

        launch = 1
        if launch_max:
            launch = self.max_threads

        while launch > 0:
            if not self.poll_queue:
                self.poll_queue = self.pending_list
            tid = self.poll_queue[0]
            self.poll_queue = self.poll_queue[1:]
            th = server.rcd.system.poll_pending(tid)
            th.connect("ready",
                       lambda x: self.process_pending(x.get_result()))
            launch -= 1
        

    def process_pending(self, pending):
        if self.finished_polling:
            return
        
        self.poll_results[pending["id"]] = pending

        if len(self.poll_results) == len(self.pending_list):
            results = self.poll_results.values()
            polling = 0
            for p in results:
                if p["is_active"]:
                    polling = 1
            if not polling:
                self.finished_polling = 1
            self.update_from_pendings(results,
                                      show_size=self.show_size,
                                      show_rate=self.show_rate)
        else:
            self.update_pulse()
                        

    def poll_worker(self):

        self.launch_poll_threads()

        if self.finished_polling:
            red_serverlistener.thaw_polling()
            return 0

        return 1


##############################################################################

class PollPending_Transact:

    def __init__(self, transact_id, step_id, callback, *cb_args):
        self.__callback = callback
        self.__cb_args = cb_args
        self.__transact_pending = None
        self.__step_pending = None
        self.__count = 0

        serv = rcd_util.get_server_proxy()
        tran_th = serv.rcd.system.poll_pending(transact_id)
        step_th = serv.rcd.system.poll_pending(step_id)

        tran_th.connect("ready",
                        lambda th, ppt: \
                        ppt.set_transact_pending(th.get_result()), self)
        step_th.connect("ready",
                        lambda th, ppt: \
                        ppt.set_step_pending(th.get_result()), self)

    def set_transact_pending(self, pending):
        self.__transact_pending = pending
        self.__count += 1
        self.finish()

    def set_step_pending(self, pending):
        self.__step_pending = pending
        self.__count += 1
        self.finish()

    def finish(self):
        self.__callback(self.__transact_pending,
                        self.__step_pending,
                        *self.__cb_args)


class PendingView_Transaction(PendingView):

    def __init__(self, download_id, transact_id, step_id, parent=None):
        PendingView.__init__(self, _("Updating System"),
                             allow_cancel=1, parent=parent,
                             total_progress_bar=1)

        self.download_id = download_id
        self.transact_id = transact_id
        self.step_id     = step_id

        self.download_complete = 0
        self.__working_query = 0
        self.__finished = 0

        self.total_percent = 0

        self.iconified = 0
        self.connect("window-state-event",
                     lambda x,y:x.window_state_event_cb(y))

        self.set_icons(("spinning-rupert-1",
                        "spinning-rupert-2",
                        "spinning-rupert-3"))
        
        red_serverlistener.freeze_polling()
        self.start_polling() # this is a different kind of polling

    def window_state_event_cb(self, ev):
        if ev.new_window_state & gtk.gdk.WINDOW_STATE_ICONIFIED:
            self.iconified = 1
        else:
            self.iconified = 0
            self.set_title(self.window_title)

    def update_from_pendings(self, pending_list, show_size=1, show_rate=1):
        update_info = PendingView.update_from_pendings(self, pending_list,
                                                       show_size, show_rate)

        (percent, elapsed_sec, remaining_sec,
         completed_size, total_size) = update_info

        if self.iconified and percent != -1:
            title = "%.1f%%" % percent
            
            if completed_size != -1 and total_size != -1:
                cs = rcd_util.byte_size_to_string(completed_size)
                ts = rcd_util.byte_size_to_string(total_size)

                title += " - %s / %s" % (cs, ts)

            title += " - " + self.window_title

            self.set_title(title)

    def cancelled(self):
        PendingView.cancelled(self)
        
        if self.download_id == -1 or self.download_complete:
            print "Can't abort transaction"
            return

        serv = rcd_util.get_server()

        try:
            ret = serv.rcd.packsys.abort_download(self.download_id)
        except ximian_xmlrpclib.Fault, f:
            ## FIXME: This is really ugly hack, but otherwise ui will be
            ## unresponsive if connection with rcd is lost (even if rcd
            ## comes back).
            rcd_util.dialog_from_fault(f)
            ret = 1

        if ret:
            print "Download aborted"
            self.stop_polling()
            self.transaction_finished(msg=_("Download cancelled"),
                                      title=_("Transaction cancelled"))
        else:
            print "Couldn't abort download"

    def finished(self):
        red_serverlistener.thaw_polling(do_immediate_poll=1)
        PendingView.finished(self)

    def poll_worker(self):

        if self.__finished:
            return 0

        # We can't cancel once the transaction begins
        if self.download_id == -1 or self.download_complete:
            self.disable_cancellation()

        if self.download_id != -1 and not self.download_complete:
            self.update_download()
        elif self.transact_id == -1:
            # We're in "download only" mode.
            if self.download_complete:
                return 0
            elif self.download_id == -1:
                # Everything we wanted to download is already cached on the
                # system.
                #
                # FIXME: Do something intelligent here?
                return 0
        else:
            return self.update_transaction()

        return 1


    def transaction_finished(self, msg, title=_("Transaction Finished")):
        self.finished()
        self.switch_cancel_button_to_ok()
        self.set_title(title)
        self.set_label(msg)
        self.step_label.set_selectable(1)
        self.update_fill()

    def update_download(self):

        if self.__working_query:
            return

        self.step_label.set_text(_("Downloading packages"))

        def download_pending_cb(th, pv):
            pv.__working_query = 0
            pending = th.get_result()
            pv.update_from_pending(pending)
            pv.update_total(pending["percent_complete"] * DOWNLOAD_MULTIPLIER)
            if pending["status"] == "finished":
                pv.download_complete = 1
                pv.update_fill()
            elif pending["status"] == "failed":
                pv.download_complete = 1
                pv.__finished = 1
                msg = _("Download Failed") + ":\n"                
                msg += pending.get("error_msg", _("Unknown Error"))
                pv.transaction_finished(msg)
                
        serv = rcd_util.get_server_proxy()
        th = serv.rcd.system.poll_pending(self.download_id)
        th.connect("ready", download_pending_cb, self)
        self.__working_query = 1
        
    def update_transaction(self):

        if self.__finished:
            self.stop_icon_anim()
            return 0

        if self.__working_query:
            return 1

        self.set_title(_("Processing Transaction"))

        def update_pending_cb(pending, step_pending, pv):
            if pv.__finished:
                return

            if pending and pending["messages"]:
                msg = rcd_util.transaction_status(pending["messages"][-1])
                pv.set_label(msg)
            if step_pending:
                if step_pending["status"] == "running":
                    pv.update_from_pending(step_pending, show_rate=0)
                else:
                    pv.update_pulse()

            if pending:
                if pv.download_complete:
                    percent = DOWNLOAD_MULTIPLIER * 100 + \
                              pending["percent_complete"] * (1 - DOWNLOAD_MULTIPLIER)
                else:
                    percent = pending["percent_complete"]

                if step_pending \
                   and pending.has_key("total_size"):
                    slice = 1.0 / pending["total_size"]

                    if pv.download_complete:
                        slice *= 1 - DOWNLOAD_MULTIPLIER

                    percent += slice * step_pending["percent_complete"]

                # We don't get step_pending notification every time, but
                # we never want to reduce the total progress bar
                if percent > self.total_percent:
                    pv.update_total(percent)
                    self.total_percent = percent

            if pending and pending["status"] == "finished":
                red_pendingops.clear_packages_with_actions()
                pv.transaction_finished(msg=_("The transaction has " \
                                        "completed successfully"))
                self.update_total(100)
                pv.__finished = 1
            elif pending and pending["status"] == "failed":
                msg = _("Transaction failed") + ":\n" + pending["error_msg"]
                pv.transaction_finished(msg,
                                        title=_("Transaction Failed"))
                pv.__finished = 1

            if pending and step_pending:
                pv.__working_query = 0


        unused = PollPending_Transact(self.transact_id,
                                      self.step_id,
                                      update_pending_cb,
                                      self)
        self.__working_query = 1

        return 1
