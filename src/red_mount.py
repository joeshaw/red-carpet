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

def mount_channel(path):
    server = rcd_util.get_server()

    path_base = os.path.basename(path)
    alias = string.lower(path_base)

    aliases = map(rcd_util.get_channel_alias, rcd_util.get_all_channels())

    old_alias = alias
    count = 1
    while alias in aliases:
        alias = "%s%d" % (old_alias, count)
        count += 1

    cid = server.rcd.packsys.mount_directory(path, path, alias)

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

COLUMN_CID  = 0
COLUMN_ICON = 1
COLUMN_NAME = 2

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
                              gobject.TYPE_STRING)

        for c in channels:
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

        selection = view.get_selection()
        selection.set_mode("multiple")

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.show()

        sw.add(view)
        self.vbox.pack_start(sw)

        b = self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        b.connect("clicked", lambda x,y:y.destroy(), self)

        b = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        def ok_clicked_cb(b, w, s):
            
            def selected_rows_cb(model, path, iter, channels):
                channels.append(model.get_value(iter, COLUMN_CID))
                
            channels = []
            s.selected_foreach(selected_rows_cb, channels)
            for c in channels:
                unmount_channel(c)

            w.destroy()

        b.connect("clicked", ok_clicked_cb, self, selection)
