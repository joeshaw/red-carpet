###
### Copyright 2003 Ximian, Inc.
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

import rcd_util
import red_dirselection

mounted_channels = []

def mount_channel(path, name=None):
    server = rcd_util.get_server()

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

    cid = server.rcd.packsys.mount_directory(path, name, alias)

    if not cid:
        dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR,
                                   gtk.BUTTONS_OK,
                                   "Unable to mount %s as a channel" % path)
        dialog.run()
        dialog.destroy()
    else:
        mounted_channels.append(cid)

def unmount_channel(cid):
    server = rcd_util.get_server()

    success = server.rcd.packsys.unmount_directory(cid)
    if not success:
        dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR,
                                   gtk.BUTTONS_OK,
                                   "Unable to unmount %s" % rcd_util.get_channel_name(cid))
        dialog.run()
        dialog.destroy()
    else:
        if cid in mounted_channels:
            mounted_channels.remove(cid)

def select_and_mount():
    def get_file_cb(b, ds):
        [mount_channel(x) for x in ds.get_selections()]
        ds.destroy()

    dirsel = red_dirselection.DirSelection("Mount Directory")
    dirsel.ok_button.connect("clicked", get_file_cb, dirsel)
    dirsel.cancel_button.connect("clicked", lambda x,y:y.destroy(), dirsel)
    dirsel.show()

def has_mounted_channels():
    channels = mounted_channels
    if len(channels):
        return 1

    # Try a bit harder
    server = rcd_util.get_server()
    channels += [x["id"] for x in server.rcd.packsys.get_channels()
                 if x.get("transient", 0) and not x["id"] in mounted_channels]
    return len(channels)


class FileEntry(gtk.HBox):

    def __init__(self):
        gtk.HBox.__init__(self)
        self.build()

    def build(self):
        self.entry = gtk.Entry()
        self.pack_start(self.entry)
        self.entry.show()

        button = gtk.Button("Browse...")
        self.pack_start(button)
        button.connect("clicked", self.browse)
        button.show()

    def browse(self, button):
        def get_file_cb(b, this):
            file = this.dirsel.get_selections()
            self.entry.set_text(file[0])
            self.dirsel.destroy()

        self.dirsel = red_dirselection.DirSelection("Mount Directory")
        self.dirsel.set_select_multiple(0)
        self.dirsel.ok_button.connect("clicked", get_file_cb, self)
        self.dirsel.cancel_button.connect("clicked", lambda x,y:y.destroy(), self.dirsel)
        self.dirsel.show()

    def get_entry(self):
        return self.entry

class MountWindow(gtk.Dialog):

    def __init__(self):
        gtk.Dialog.__init__(self)
        self.build()

    def build(self):
        frame = gtk.Frame("Mount a directory as channel")
        frame.set_border_width(5)

        table = gtk.Table(2, 2)
        table.set_border_width(5)
        table.set_col_spacings(5)
        table.set_row_spacings(5)

        l = gtk.Label("Channel Name:")
        l.set_alignment(0, 0.5)
        table.attach_defaults(l, 0, 1, 0, 1)

        l = gtk.Label("Directory:")
        l.set_alignment(0, 0.5)
        table.attach_defaults(l, 0, 1, 1, 2)

        self.channel = gtk.Entry()
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
            dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR,
                                       gtk.BUTTONS_OK,
                                       "Please choose the path for channel.")
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

        gtk.Dialog.__init__(self)

        self.set_default_size(300, 300)

        server = rcd_util.get_server()

        channels = mounted_channels
        channels += [x["id"] for x in server.rcd.packsys.get_channels()
                     if x.get("transient", 0) and not x["id"] in mounted_channels]

        model = gtk.ListStore(gobject.TYPE_INT,
                              gtk.gdk.Pixbuf,
                              gobject.TYPE_STRING,
                              gobject.TYPE_BOOLEAN)

        channels_to_unmount = {}
        for c in channels:
            channels_to_unmount[c] = 0
            iter = model.append()
            model.set_value(iter, COLUMN_CID, c)
            model.set_value(iter, COLUMN_ICON, rcd_util.get_channel_icon(c))
            model.set_value(iter, COLUMN_NAME, rcd_util.get_channel_name(c))

        col = gtk.TreeViewColumn()
        col.set_title("Channel")

        r = gtk.CellRendererPixbuf()
        col.pack_start(r, 0)
        col.set_attributes(r, pixbuf=COLUMN_ICON)

        r = gtk.CellRendererText()
        col.pack_start(r, 0)
        col.set_attributes(r, text=COLUMN_NAME)

        view = gtk.TreeView(model)
        view.append_column(col)
        view.show()

        def activate_cb(renderer, path, model):
            path = (int(path),)
            node = model.get_iter(path)
            cid = model.get_value(node, COLUMN_CID)
            active = not renderer.get_active()
            channels_to_unmount[cid] = active
            model.set_value(node, COLUMN_UNMOUNT, active)

        r = gtk.CellRendererToggle()
        r.set_property("activatable", 1)
        r.connect("toggled", activate_cb, model)
        col = gtk.TreeViewColumn("Unmount?", r, active=COLUMN_UNMOUNT)
        view.append_column(col)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.show()

        sw.add(view)
        self.vbox.pack_start(sw)

        b = self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        b.connect("clicked", lambda x,y:y.destroy(), self)

        b = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        def ok_clicked_cb(b, w, s):
            for cid in s.keys():
                if s[cid]:
                    unmount_channel(cid)
            
            w.destroy()

        b.connect("clicked", ok_clicked_cb, self, channels_to_unmount)
