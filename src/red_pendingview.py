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

import string, threading, gobject, gtk
import rcd_util
import red_pendingops, red_serverlistener

class PendingView(gtk.Window):

    def __init__(self, title=None, label=None,
                 parent=None,
                 timeout_len=200, show_rate=1, show_size=1, is_modal=1,
                 allow_cancel=0,
                 self_destruct=0):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

        self.set_default_size(350, 150)
        self.set_modal(is_modal)

        self.window_parent = parent
        if parent:
            self.set_transient_for(parent)
        self.position_window()

        self.pending_list = []
        self.polling_timeout = 0
        self.finished_lag = 600

        self.timeout_len = timeout_len
        self.show_rate = show_rate
        self.show_size = show_size
        self.self_destruct = self_destruct
        self.allow_cancel = allow_cancel

        self.ourframe = gtk.Frame()
        self.add(self.ourframe)

        self.mainbox = gtk.VBox(0, 10)
        self.mainbox.set_border_width(10)
        self.ourframe.add(self.mainbox)

        self.window_title = title
        self.title_label = gtk.Label("")
        self.title_label.set_alignment(0, 0.5)
        self.mainbox.pack_start(self.title_label, 0, 0, 0)
        self.set_title(self.window_title)

        self.step_label = gtk.Label("")
        self.step_label.set_alignment(0, 0.5)
        self.mainbox.pack_start(self.step_label, 0, 0, 0)
        if label:
            self.set_label(label)

        self.progress_bar = gtk.ProgressBar()
        self.mainbox.pack_start(self.progress_bar, 0, 0, 0)

        self.button = None
        if self.allow_cancel or not self.self_destruct:
            bbox = gtk.HButtonBox()
            bbox.set_layout(gtk.BUTTONBOX_END)
            self.mainbox.pack_end(bbox, 0, 0, 0)
            if self.allow_cancel:
                self.button = gtk.Button(gtk.STOCK_CANCEL)
                self.button.cancel = 1
            else:
                self.button = gtk.Button(gtk.STOCK_OK)
                self.button.cancel = 0
                self.button.set_sensitive(0)
            self.button.set_use_stock(1)
            bbox.pack_start(self.button, 0, 0, 0)

            def button_handler_cb(b, pv):
                if b.cancel:
                    pv.cancelled()
                else:
                    pv.finished()
            self.button.connect("clicked", button_handler_cb, self)

        self.ourframe.show_all()

    def position_window(self):
        if self.window_parent:
            self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        else:
            self.set_position(gtk.WIN_POS_CENTER)

    def disable_cancellation(self):
        if self.allow_cancel:
            self.button.set_sensitive(0)

    def cancelled(self):
        print "Cancelled!"

    def finished(self):
        self.emit("finished")
        print "Finished!"
        self.destroy()

    def set_title(self, msg):
        gtk.Window.set_title(self, msg)
        self.title_label.set_markup("<b><big>%s</big></b>" % (msg or ""))
        self.position_window() # keep window centered

    def set_label(self, msg):
        if msg:
            lines = rcd_util.linebreak(msg, 40)
            msg = string.join(lines, "\n")
        else:
            msg = ""
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

            if show_size:
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

    # Define me!
    def poll_worker(self):
        return 0

    def switch_cancel_button_to_ok(self):
        if self.button.cancel:
            self.button.set_label(gtk.STOCK_OK)
            self.button.cancel = 0

    def poll(self):

        polling = self.poll_worker()

        if not polling:
            def finished_cb(x):
                if x.self_destruct:
                    x.finished()
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
                             self_destruct=1, allow_cancel=0)

        self.pending_list = []

        self.max_threads = 5

        self.pending_countdown = 0
        self.poll_queue = []
        self.poll_results = {}
        self.first_poll = 1
        self.finished_polling = 0

    def set_pending_list(self, pending_list):
        self.pending_list = pending_list
        self.start_polling()
        red_serverlistener.freeze_polling()

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

        self.launch_poll_threads()

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

        if self.first_poll:
            self.launch_poll_threads(launch_max=1)
            self.first_poll = 0

        if self.finished_polling:
            red_serverlistener.thaw_polling()
            self.first_poll = 1
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
        PendingView.__init__(self, "Updating System",
                             allow_cancel=1, parent=parent)

        self.download_id = download_id
        self.transact_id = transact_id
        self.step_id     = step_id

        self.download_complete = 0
        self.__working_query = 0
        self.__finished = 0

        self.iconified = 0
        self.connect("window-state-event",
                     lambda x,y:x.window_state_event_cb(y))

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
        if self.download_id == -1 or self.download_complete:
            print "Can't abort transaction"
            return

        serv = rcd_util.get_server()
        ret = serv.rcd.packsys.abort_download(self.download_id)

        if ret:
            print "Download aborted"
            self.stop_polling()
            self.transaction_finished(msg="Download cancelled",
                                      title="Update cancelled")
        else:
            print "Couldn't abort download"

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


    def transaction_finished(self, msg, title="Update Finished"):
        self.switch_cancel_button_to_ok()
        self.set_title(title)
        self.set_label(msg)
        self.update_fill()
        red_serverlistener.thaw_polling(do_immediate_poll=1)

    def update_download(self):

        if self.__working_query:
            return

        self.step_label.set_text("Downloading packages")

        def download_pending_cb(th, pv):
            pv.__working_query = 0
            pending = th.get_result()
            pv.update_from_pending(pending)
            if pending["status"] == "finished":
                pv.download_complete = 1
                pv.update_fill()
            elif pending["status"] == "failed":
                pv.download_complete = 1
                pv.transaction_finished("Download Failed")
                
        serv = rcd_util.get_server_proxy()
        th = serv.rcd.system.poll_pending(self.download_id)
        th.connect("ready", download_pending_cb, self)
        self.__working_query = 1
        
    def update_transaction(self):

        if self.__finished:
            return 0

        if self.__working_query:
            return 1

        self.set_title("Processing Transaction")
        self.set_label("Starting Transaction")

        def update_pending_cb(pending, step_pending, pv):
            if pending and step_pending:
                pv.__working_query = 0
                
            if pending and pending["messages"]:
                msg = rcd_util.transaction_status(pending["messages"][-1])
                pv.set_label(msg)
            if step_pending and step_pending["status"] == "running":
                pv.update_from_pending(step_pending, show_rate=0)
            else:
                pv.update_pulse()

            if pending and pending["status"] == "finished":
                red_pendingops.clear_packages_with_actions()
                pv.transaction_finished(msg="The update has " \
                                        "completed successfully")
                pv.__finished = 1
            elif pending and pending["status"] == "failed":
                msg = "Transaction failed: %s" % pending["error_msg"]
                pv.transaction_finished(msg)
                self.__finished = 1

        unused = PollPending_Transact(self.transact_id,
                                      self.step_id,
                                      update_pending_cb,
                                      self)

        return 1

                       
