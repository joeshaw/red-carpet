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
import red_transaction

class PendingView(gtk.Window):

    def __init__(self, title=None, label=None,
                 parent=None,
                 timeout_len=400, show_rate=1, show_size=1, is_modal=1,
                 allow_cancel=0,
                 self_destruct=0):
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
        self.self_destruct = self_destruct
        self.allow_cancel = allow_cancel

        self.ourframe = gtk.Frame()
        self.add(self.ourframe)

        self.mainbox = gtk.VBox(0, 10)
        self.mainbox.set_border_width(10)
        self.ourframe.add(self.mainbox)

        self.title_label = gtk.Label("")
        self.title_label.set_alignment(0, 0.5)
        self.mainbox.pack_start(self.title_label, 0, 0, 0)
        self.set_title(title)

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

    def cancelled(self):
        print "Cancelled!"

    def finished(self):
        print "Finished!"
        self.destroy()

    def set_title(self, msg):
        self.title_label.set_markup("<b><big>%s</big></b>" % (msg or ""))

    def set_label(self, msg):
        self.step_label.set_text(msg or "")

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

    def update(self, percent,
               elapsed_sec, remaining_sec,
               completed_size, total_size,
               show_size=1, show_rate=1):

        if percent <= 0:
            self.progress_bar.set_text("")
            self.progress_bar.pulse()
        else:
            rate = 0
            if elapsed_sec > 0:
                rate = completed_size / elapsed_sec

            self.progress_bar.set_fraction(percent / 100.0)

            msg = "%.1f%%" % percent

            if show_rate and total_size > 0 and rate > 0:
                rate_str = rcd_util.byte_size_to_string(rate) + "/s"
            else:
                rate_str = None

            if show_size and total_size > 0:
                cs = rcd_util.byte_size_to_string(completed_size)
                ts = rcd_util.byte_size_to_string(total_size)
                msg = msg + " - %s / %s" % (cs, ts)
                if rate_str:
                    msg = msg + " (" + rate_str + ")"
            else:
                if rate_str:
                    msg = msg + " - " + rate_str

            self.progress_bar.set_text(msg)


    def update_from_pendings(self, pending_list,
                             show_size=1, show_rate=1):

        rate = 0
        percent = 0
        elapsed_sec = 0
        remaining_sec = 0
        completed_size = 0
        total_size = 0

        for pending in pending_list:
            if pending["is_active"]:
                percent = percent + pending["percent_complete"]
            else:
                percent = percent + 100

            elapsed_sec = max(elapsed_sec, pending.get("elapsed_sec", 0))
            remaining_sec = max(remaining_sec, pending.get("remaining_sec", 0))

            completed_size = completed_size + pending.get("completed_size", 0)
            total_size = total_size + pending.get("total_size", 0)

        if pending_list:
            percent = percent / len(pending_list)
            self.update(percent, elapsed_sec, remaining_sec,
                        completed_size, total_size,
                        show_size=show_size, show_rate=show_rate)


    def update_from_pending(self, pending, show_size=1, show_rate=1):
        update_from_pendings([pending],
                             show_size=show_size, show_rate=show_rate)

    # Define me!
    def poll_worker(self):
        return 0

    def poll(self):

        polling = self.poll_worker()

        if not polling:
            def finished_cb(x):
                x.emit("finished")
                if x.self_destruct:
                    x.finished()
                else:
                    # If necessary, change the button from "Cancel"
                    # to "OK".  Make sure the button sensitive.
                    if x.button.cancel:
                        x.button.set_label(gtk.STOCK_OK)
                        x.button.cancel = 0
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

    def set_pending_list(self, pending_list):
        self.pending_list = pending_list
        self.start_polling()

    def poll_worker(self):
        print "Polling!"
        server = rcd_util.get_server()
        polling = 0
        pendings = []
        for tid in self.pending_list:
            pending = server.rcd.system.poll_pending(tid)
            pendings.append(pending)
            if pending["is_active"]:
                polling = 1

        self.update_from_pendings(pendings,
                                  show_size=self.show_size,
                                  show_rate=self.show_rate)

        return polling

##############################################################################

class PendingView_Transaction(PendingView):

    def __init__(self, download_id, transact_id, step_id):
        PendingView.__init__(self, "Updating System",
                             allow_cancel=1)

        self.download_id = download_id
        self.transact_id = transact_id
        self.step_id     = step_id

        self.download_complete = 0

    def abort_download(self):

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

        print "Polling..."

        if self.download_complete:
            #self.button.set_sensitive(0)
            print "Need to disable cancellation here"

        try:
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
        except red_transaction.TransactionFailed, e:
            self.transaction_finished(msg=e.message, title="Update Failed")
            return 0
            
        return 1


    def transaction_finished(self, msg, title="Update Finished"):

        self.set_title(title)
        self.set_label(msg)
        #self.progress_bar.set_fraction(1.0)
        #self.progress_bar.set_text("")

        # Restart the polling of the daemon.
        red_serverlistener.thaw_polling()


    def update_download(self):
        serv = rcd_util.get_server()
        pending = serv.rcd.system.poll_pending(self.download_id)

        self.step_label.set_text("Downloading packages")

        self.update_from_pending(pending)

        if pending["status"] == "finished":
            self.download_complete = 1
            #self.progress_bar.set_fraction(1.0)
            #self.progress_bar.set_text("")
        elif pending["status"] == "failed":
            self.download_complete = 1
            raise red_transaction.TransactionFailed, "Download failed"
        
    def update_transaction(self):
        serv = rcd_util.get_server()
        pending = serv.rcd.system.poll_pending(self.transact_id)
        step_pending = serv.rcd.system.poll_pending(self.step_id)

        self.set_title("Processing Transaction")
        self.set_label(rcd_util.transaction_status(pending["messages"][-1]))

        if step_pending["status"] == "running":
            self.update_from_pending(step_pending, show_rate=0)

        if pending["status"] == "finished":
            red_pendingops.clear_packages_with_actions()
            self.transaction_finished(msg="The update has completed successfully")
            return 0
        elif pending["status"] == "failed":
            raise red_transaction.TransactionFailed, "Transaction failed: %s" % pending["error_msg"]

        return 1

                       
