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

import string, gtk
import rcd_util
import red_packagearray, red_packageview
import red_pendingops
import red_component


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

    def __init__(self, app):
        gtk.HBox.__init__(self)
        red_pendingops.PendingOpsListener.__init__(self)
        self.app = app
        self.label = gtk.Label(TransactionBar.no_action_str)
        self.pack_end(self.label, 0, 0, 2)
        self.label.show()

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
        self.app.sensitize_go_button(msg != "")

    def pendingops_changed(self, pkg, key, value, old_value):
        if key == "action":
            self.update_label()
    
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

class TransactionComponent(red_component.Component):

    def name(self):
        return "Pending Transactions"

    def long_name(self):
        return "Manage Pending Transactions"

    def pixbuf(self):
        return "about-monkey"

    def show_on_toolbar(self):
        return 1

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

        return scrolled


    def changed_visibility(self, flag):

        if not flag:
            red_pendingops.clear_action_cancellations()

