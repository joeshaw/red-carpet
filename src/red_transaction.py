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
import red_packagearray, red_packageview
import red_pendingops
import red_component
import red_depwindow
import red_main

class TransactionArray(red_packagearray.PackageArray,
                       red_pendingops.PendingOpsListener):

    def __init__(self):
        self.packages = red_pendingops.packages()
        red_packagearray.PackageArray.__init__(self)
        red_pendingops.PendingOpsListener.__init__(self)

    def sort(self, sort_fn, reverse):
        self.packages.sort(sort_fn)
        if reverse:
            self.packages.reverse()

    def get_all(self):
        return self.packages

    def pendingops_changed(self, pkg, key, value, old_value):
        def refresh_op(self):
            self.packages = red_pendingops.packages_with_actions()
        self.changed(refresh_op)

#########################################################################

class TransactionBar(gtk.HBox,
                     red_pendingops.PendingOpsListener):

    no_action_str = "No Pending Actions"

    def __init__(self):
        gtk.HBox.__init__(self)
        red_pendingops.PendingOpsListener.__init__(self)
        self.button = gtk.Button("Go!")
        self.button.set_sensitive(0)
        self.label = gtk.Label(TransactionBar.no_action_str)
        self.pack_end(self.button, 0, 0, 2)
        self.pack_end(self.label, 0, 0, 2)
        self.label.show()

        def clicked_cb(x):
            depwindow = red_depwindow.DepWindow()
            depwindow.show()
            
        self.button.connect("clicked", clicked_cb)

    def update_label(self):
        msg_list = []

        ins_count = red_pendingops.pending_install_count()
        if ins_count:
            msg_list.append("%d pending install%s" %
                            (ins_count,
                             (ins_count > 1 and "s") or ""))

        rem_count = red_pendingops.pending_remove_count()
        if rem_count:
            msg_list.append("%d pending removal%s" %
                            (rem_count,
                             (rem_count > 1 and "s") or ""))
                
        msg = string.join(msg_list, ", ")
        self.label.set_text(msg or TransactionBar.no_action_str)
        self.button.set_sensitive(msg != "")

    def pendingops_changed(self, pkg, key, value, old_value):
        if key == "action":
            self.update_label()
    

#########################################################################

class TransactionComponent(red_component.Component):

    def name(self):
        return "Pending Transactions"

    def pixbuf(self):
        return "about-monkey"

    def build(self):
        self.array = TransactionArray()

        view = red_packageview.PackageView()
        view.append_action_column()
        view.append_name_column(show_channel_icon=1)
        view.append_version_column()
        view.append_size_column()

        def act_cb(view, i, pkg):
            red_pendingops.toggle_action_with_cancellation(pkg)
        view.set_activated_fn(act_cb)
        
        view.set_model(self.array)

        scrolled = gtk.ScrolledWindow()
        scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled.add(view)
        view.show()

        self.display("main", scrolled)


    def changed_visibility(self, flag):

        if not flag:
            red_pendingops.clear_action_cancellations()
            
#########################################################################

def ok_to_quit(main_app_window):

    ins = red_pendingops.pending_install_count()
    rem = red_pendingops.pending_remove_count()

    if ins == 0 and rem == 0:
        return 1

    msgs = []
    if ins > 0:
        msgs.append("%d pending install%s" % (ins, (ins > 1 and "s") or ""))
    if rem > 0:
        msgs.append("%d pending removal%s" % (rem, (rem > 1 and "s") or ""))

    if (ins == 1 and rem == 0) or (ins == 0 and rem == 1):
        word = "is"
    else:
        word = "are"
    count_msg  = "There %s currently %s.  If you quit now, all pending " \
                 "actions will be lost." % (word, string.join(msgs, " and "))

    msg_lines = rcd_util.linebreak(count_msg, 40)
    msg_lines.append("Are you sure you want to quit?")
    
    msgbox = gtk.VBox(0, 0)
    msgbox.pack_start(gtk.HBox(0, 0), 0, 0, 4) # shim
    for line in msg_lines:
        label = gtk.Label(line)
        label.set_alignment(0, 0.5)
        msgbox.pack_start(label, 1, 0, 1)
    msgbox.pack_start(gtk.HBox(0, 0), 0, 0, 4) # shim

    img = gtk.Image()
    img.set_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG)

    main_box = gtk.HBox(0, 0)

    main_box.pack_start(gtk.HBox(0, 0), 0, 0, 4) # shim
    main_box.pack_start(img, 0, 0, 5)
    main_box.pack_start(msgbox, 1, 1, 5)
    main_box.pack_start(gtk.HBox(0, 0), 0, 0, 4) # shim
    main_box.show_all()
        
    dialog = gtk.Dialog("")
    dialog.add_button(gtk.STOCK_CANCEL, 0)
    dialog.add_button(gtk.STOCK_QUIT, 1)
    dialog.vbox.add(main_box)
    
    dialog.show()
    retval = dialog.run()
    dialog.destroy()

    return retval

#########################################################################

class TransactionFailed(Exception):
    def __init__(self, message):
        self.message = message

    def __repr__(self):
        return "<TransactionFailed '%s'>" % self.message

timeout_len = 400

class TransactionWindow(gtk.Window):

    def __init__(self, download_id, transact_id, step_id):

        gtk.Window.__init__(self)

        self.download_id = download_id
        self.transact_id = transact_id
        self.step_id = step_id

        self.download_complete = 0

        self.set_title("%s - Updating System" % red_main.red_name)
        self.set_default_size(400, 250)
        self.set_modal(1)

        # shim
        hbox = gtk.HBox(0, 10)
        self.add(hbox)
        hbox.show()

        self.mainbox = gtk.VBox(0, 10)
        hbox.pack_start(self.mainbox)

        self.title_label = gtk.Label("")
        self.title_label.set_markup("<b><big>Updating System</big></b>")
        self.title_label.set_alignment(0, 0.5)
        self.mainbox.pack_start(self.title_label, 0, 0, 0)

        self.step_label = gtk.Label("")
        self.step_label.set_alignment(0, 0.5)
        self.mainbox.pack_start(self.step_label, 0, 0, 0)

        self.progress_bar = gtk.ProgressBar()
        self.mainbox.pack_start(self.progress_bar, 0, 0, 0)

        self.progress_text = gtk.Label("")
        self.progress_text.set_alignment(0, 0.5)
        self.mainbox.pack_start(self.progress_text, 0, 0, 0)

        bbox = gtk.HButtonBox()
        bbox.set_layout(gtk.BUTTONBOX_END)
        self.mainbox.pack_end(bbox, 0, 0, 0)

        self.button = gtk.Button(gtk.STOCK_CANCEL)
        self.button.set_use_stock(1)
        self.button.cancel = 1
        bbox.pack_start(self.button, 0, 0, 0)

        def clicked_cb(button, window):
            if button.cancel:
                window.abort_download()
            else:
                window.destroy()

        self.button.connect("clicked", clicked_cb, self)

        self.show_all()

        def poll_cb():
            return self.poll_transaction()

        self.poll_id = gtk.timeout_add(timeout_len, poll_cb)

    def abort_download(self):
        if self.download_id == -1 or self.download_complete:
            print "Can't abort transaction"
            return

        serv = rcd_util.get_server()
        ret = serv.rcd.packsys.abort_download(self.download_id)

        if ret:
            print "Download aborted"
            gtk.timeout_remove(self.poll_id)
            self.transaction_finished(msg="Download cancelled",
                                      title="Update Cancelled")
        else:
            print "Couldn't abort download"

    def poll_transaction(self):

        print "Polling..."

        if self.download_complete:
            self.button.set_sensitive(0)

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
        except TransactionFailed, e:
            self.transaction_failed(msg=e.message, title="Update Failed")

            return 0
            
        return 1

    def update_progress_from_pending(self, pending, show_rate=1):
        if pending.has_key("completed_size") and pending.has_key("total_size"):
            fraction = float(pending["completed_size"]) / float(pending["total_size"])
            self.progress_bar.set_fraction(fraction)

            cs = rcd_util.byte_size_to_string(pending["completed_size"])
            ts = rcd_util.byte_size_to_string(pending["total_size"])
            msg = "%s / %s" % (cs, ts)

            if show_rate and pending.has_key("elapsed_sec") and \
                   pending.has_key("completed_size"):
                elap = pending["elapsed_sec"]
                if elap > 0:
                    rate = rcd_util.byte_size_to_string(
                        pending["completed_size"] / elap)
                    msg = msg + " (" + rate + "/s)"
                
        else:
            self.progress_bar.pulse()
            msg = ""

        self.progress_bar.set_text(msg)

    def transaction_finished(self, msg, title="Update Finished"):
        self.progress_bar.set_fraction(1.0)
        self.progress_bar.set_text("")
        self.title_label.set_markup("<b><big>%s</big></b>" % title)
        self.step_label.set_text(msg)
        self.progress_text.set_text("")
        self.button.set_label(gtk.STOCK_OK)
        self.button.cancel = 0
        self.button.set_sensitive(1)

    def update_download(self):
        serv = rcd_util.get_server()
        pending = serv.rcd.system.poll_pending(self.download_id)

        self.step_label.set_text("Downloading packages")

        self.update_progress_from_pending(pending)

        if pending["status"] == "finished":
            self.download_complete = 1
            self.progress_bar.set_fraction(1.0)
            self.progress_bar.set_text("")
        elif pending["status"] == "failed":
            self.download_complete = 1
            raise TransactionFailed, "Download failed"
        
    def update_transaction(self):
        serv = rcd_util.get_server()
        pending = serv.rcd.system.poll_pending(self.transact_id)
        step_pending = serv.rcd.system.poll_pending(self.step_id)

        self.step_label.set_text("Processing Transaction")
        
        self.progress_text.set_markup("<i>%s</i>" % rcd_util.transaction_status(pending["messages"][-1]))

        if step_pending["status"] == "running":
            self.update_progress_from_pending(step_pending, show_rate=0)

        if pending["status"] == "finished":
            self.transaction_finished(msg="The update has completed successfully")
            return 0
        elif pending["status"] == "failed":
            raise TransactionFailed, "Transaction failed: %s" % pending["error_msg"]

        return 1
                
