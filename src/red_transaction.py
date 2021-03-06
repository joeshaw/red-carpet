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

import string, gtk
import rcd_util
import red_packagearray, red_packageview
import red_pendingops
import red_component
import red_serverlistener

from red_gettext import _

model = None

class TransactionArray(red_packagearray.PackageArray,
                       red_pendingops.PendingOpsListener,
                       red_serverlistener.ServerListener):

    def __init__(self):
        self.packages = red_pendingops.packages_with_actions()
        red_packagearray.PackageArray.__init__(self)
        red_pendingops.PendingOpsListener.__init__(self)
        red_serverlistener.ServerListener.__init__(self)
        self.__pending = 0

    def get_all(self):
        return self.packages

    def pendingops_changed(self, pkg, key, value, old_value):
        def pending_refresh_cb(array):
            def refresh_op(x):
                x.packages = red_pendingops.packages_with_actions()
            array.changed(refresh_op)
            array.__pending = 0
            return 0

        if not self.__pending:
            self.__pending = gtk.idle_add(pending_refresh_cb, self)

    def refresh(self):
        # We need to go through and delete packages in the pending actions
        # if they were going to be installed from a channel which no longer
        # exists.
        actions = (red_pendingops.TO_BE_INSTALLED,
                   red_pendingops.TO_BE_INSTALLED_CANCELLED)
        for pkg in red_pendingops.packages_with_actions(*actions):
            if not rcd_util.get_channel(pkg.get("channel", "")):
                red_pendingops.set_action(pkg, red_pendingops.NO_ACTION)

        self.changed(lambda x:x) # noop

    def channels_changed(self):
        self.refresh()

    def packages_changed(self):
        self.refresh()

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
                 "operations will be lost." % (word, string.join(msgs, " and "))

    msg_lines = rcd_util.linebreak(count_msg, 40)
    msg_lines.append(_("Are you sure you want to quit?"))
    
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
        
    dialog = gtk.Dialog("", parent=main_app_window)
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
        return _("Pending Actions")

    def menu_name(self):
        return _("_Pending Actions")

    def pixbuf(self):
        return "pending-transactions"

    def accelerator(self):
        return "<Control>P"

    def show_in_shortcuts(self):
        return 1

    def build(self):
        global model
        if not model:
            model = TransactionArray()

        self.array = model

        page = gtk.VBox(0, 6)

        view = red_packageview.PackageView(self.array)
        self.connect_view(view)
        self.view = view
        
        view.append_action_column(show_action_name=1)
        view.append_name_column(show_channel_icon=1)
        view.append_version_column()
        view.append_size_column()

        def act_cb(view, i, pkg):
            red_pendingops.toggle_action_with_cancellation(pkg)
        view.set_activated_fn(act_cb)
        
        scrolled = gtk.ScrolledWindow()
        scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled.set_shadow_type(gtk.SHADOW_IN)
        scrolled.add(view)

        page.pack_start(scrolled, expand=1, fill=1)
        page.show_all()

        return page


    def changed_visibility(self, flag):
        if not flag:
            red_pendingops.clear_action_cancellations()

    def select_all_sensitive(self):
        return self.array.len() > 0

    def select_all(self):
        selection = self.view.get_selection()
        selection.select_all()

    def unselect_all(self):
        selection = self.view.get_selection()
        selection.unselect_all()
        # In some cases, the selection's changed signal doesn't get
        # emitted when we unselect_all on it.  I'm not sure why.
        self.packages_selected([])

class TransactionSimple(gtk.ScrolledWindow):

    def __init__(self):
        gtk.ScrolledWindow.__init__(self)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_IN)

        global model
        if not model:
            model = TransactionArray()

        view = red_packageview.PackageView(model)
        view.append_action_column(show_action_name=1, activatable=0)
        view.append_name_column(show_channel_icon=1)

        view.show()

        self.add(view)
