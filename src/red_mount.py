###
### Copyright (C) 2003 Ximian, Inc.
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

import sys, os, string
import gobject, gtk

import ximian_xmlrpclib
import rcd_util
import red_channelmodel
import red_dirselection
import red_thrashingtreeview
from red_gettext import _

def mount_channel(path, name=None):
    # Handle ~ to mean $HOME
    if path[0] == "~":
        homedir = os.getenv("HOME")
        if homedir:
            path = homedir + path[1:]
            print path

    path_base = os.path.basename(path)
    alias = string.lower(path_base)

    aliases = map(rcd_util.get_channel_alias, rcd_util.get_all_channels())

    old_alias = alias
    count = 1
    while alias in aliases:
        alias = "%s%d" % (old_alias, count)
        count += 1

    if not name:
        name = path

    server = rcd_util.get_server_proxy()
    mount_th = server.rcd.packsys.mount_directory(path, name, alias)

    def mount_cb(th, path):
        try:
            cid = th.get_result()
        except ximian_xmlrpclib, f:
            rcd_util.dialog_from_fault(f)
            return
        
        if not cid:
            msg = _("Unable to mount '%s' as a channel") % path
            dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR,
                                       gtk.BUTTONS_OK, msg)

            def idle_cb(d):
                gtk.threads_enter()
                d.show()
                d.run()
                d.destroy()
                gtk.threads_leave()

            # Always run the dialog in the main thread
            gtk.idle_add(idle_cb, dialog)

    mount_th.connect("ready", mount_cb, path)


def unmount_channel(cid):

    server = rcd_util.get_server_proxy()
    unmount_th = server.rcd.packsys.unmount_directory(cid)

    def unmount_cb(th, name):
        try:
            success = th.get_result()
        except ximian_xmlrpclib.Fault, f:
            rcd_util.dialog_from_fault(f)
            return
        
        if not success:
            msg = _("Unable to unmount '%s'") % name
            dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR,
                                       gtk.BUTTONS_OK, msg)
            dialog.run()
            dialog.destroy()

    unmount_th.connect("ready", unmount_cb,
                       rcd_util.get_channel_name(cid))


def has_mounted_channels():
    return len([x["id"] for x in rcd_util.get_all_channels()
                if x.get("transient", 0)])

class FileEntry(gtk.HBox):

    def __init__(self):
        gtk.HBox.__init__(self)
        self.build()

    def build(self):
        self.entry = gtk.Entry()
        self.entry.set_activates_default(1)
        self.pack_start(self.entry)
        self.entry.show()

        button = gtk.Button(_("Browse..."))
        self.pack_start(button)
        button.connect("clicked", self.browse)
        button.show()

    def browse(self, button):
        def get_file_cb(b, this):
            file = this.dirsel.get_selections()
            self.entry.set_text(file[0])
            self.dirsel.destroy()

        self.dirsel = red_dirselection.DirSelection(_("Mount Directory"))
        self.dirsel.set_filename(os.environ.get("HOME", "") + "/")
        self.dirsel.set_select_multiple(0)
        self.dirsel.ok_button.connect("clicked", get_file_cb, self)
        self.dirsel.cancel_button.connect("clicked", lambda x,y:y.destroy(), self.dirsel)
        self.dirsel.show()

    def get_entry(self):
        return self.entry

class MountWindow(gtk.Dialog):

    def __init__(self):
        gtk.Dialog.__init__(self, _("Mount channel"))
        self.build()
        
    def build(self):
        frame = gtk.Frame(_("Mount a directory as channel"))
        frame.set_border_width(5)

        table = gtk.Table(2, 2)
        table.set_border_width(5)
        table.set_col_spacings(5)
        table.set_row_spacings(5)

        l = gtk.Label(_("Channel Name:"))
        l.set_alignment(0, 0.5)
        table.attach_defaults(l, 0, 1, 0, 1)

        l = gtk.Label(_("Directory:"))
        l.set_alignment(0, 0.5)
        table.attach_defaults(l, 0, 1, 1, 2)

        self.channel = gtk.Entry()
        self.channel.set_activates_default(1)
        table.attach_defaults(self.channel, 1, 2, 0, 1)

        self.directory = FileEntry()
        table.attach_defaults(self.directory, 1, 2, 1, 2)

        frame.add(table)
        frame.show_all()

        self.vbox.add(frame)

        button = self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        button.connect("clicked", lambda x:self.destroy())

        button = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        button.grab_default()
        button.connect("clicked", lambda x:self.mount())

    def mount(self):
        name = self.channel.get_text()

        e = self.directory.get_entry()
        path = e.get_text()

        if not path:
            dialog = gtk.MessageDialog(self, 0, gtk.MESSAGE_ERROR,
                                       gtk.BUTTONS_OK,
                                       _("Please choose the path for channel."))
            dialog.run()
            dialog.destroy()
            return

        if not name:
            name = path

        mount_channel(path, name)
        self.destroy()


COLUMN_CID  =    0
COLUMN_ICON =    1
COLUMN_NAME =    2
COLUMN_UNMOUNT = 3

class UnmountWindow(gtk.Dialog):

    def __init__(self):

        gtk.Dialog.__init__(self, _("Unmount Channel"))

        self.set_default_size(300, 300)

        model = red_channelmodel.ChannelModel(filter_fn=lambda x:x["transient"])

        channels_to_unmount = {}
        for c in model.get_all():
            channels_to_unmount[c["id"]] = 0

        umount_col = model.add_column(lambda x:channels_to_unmount[x["id"]],
                                      gobject.TYPE_BOOLEAN)

        view = red_thrashingtreeview.TreeView(model)

        r = gtk.CellRendererText()
        col = gtk.TreeViewColumn(_("Channel"), r, text=COLUMN_NAME)
        view.append_column(col)

        def toggle_cb(cr, path, mod):
            def set_cb(m, p):
                c = m.get_list_item(int(p))
                channels_to_unmount[c["id"]] = not channels_to_unmount[c["id"]]
            mod.changed(set_cb, path)

        r = gtk.CellRendererToggle()
        r.set_property("activatable", 1)
        r.set_property("xalign", 0.0)
        r.connect("toggled", toggle_cb, model)
        col = gtk.TreeViewColumn(_("Unmount?"), r, active=umount_col)
        view.append_column(col)

        view.show()

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_IN)
        sw.show()

        sw.add(view)
        self.vbox.pack_start(sw)

        b = self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        b.connect("clicked", lambda x,y:y.destroy(), self)

        b = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        b.grab_default()
        def ok_clicked_cb(b, w, s):
            for cid in s:
                if s[cid]:
                    unmount_channel(cid)
            
            w.destroy()

        b.connect("clicked", ok_clicked_cb, self, channels_to_unmount)
