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

import gtk
import gobject
import string
import re
import ximian_xmlrpclib
import rcd_util
import red_serverlistener

COLUMN_ID          = 0
COLUMN_NAME        = 1
COLUMN_ALIAS       = 2
COLUMN_SUBSCRIBED  = 3
COLUMN_ICON        = 4
COLUMN_DESCRIPTION = 5
COLUMN_LAST        = 6

def fake_alias(c):
    alias = string.strip(string.lower(c["name"]))
    alias = string.replace(alias, " ", "-")
        
    # FIXME: hackish evil to generate nicer fallback aliases.
    # This should be removed once we actually get aliases
    # into the channel XML.
    alias = re.sub("-devel[a-z]*-", "-dev-", alias)
    alias = re.sub("snapshots?", "snaps", alias)
    alias = string.replace(alias, "gnome-2.0", "gnome2")
    alias = string.replace(alias, "evolution", "evo")
    alias = string.replace(alias, "-gnome-", "-")
    if string.find(alias, "red-hat") == 0:
        alias = "redhat"
            
    return alias

def channel_cmp(a,b):
    return cmp(string.lower(a["name"]), string.lower(b["name"]))

class ChannelModel(gtk.GenericTreeModel, red_serverlistener.ServerListener):

    def __init__(self):
        gtk.GenericTreeModel.__init__(self)
        self.channels = rcd_util.get_all_channels()
        self.channels.sort(channel_cmp)

    def channel_to_column(self, channel, i):
        if i == COLUMN_ID:
            return str(channel["id"])
        elif i == COLUMN_NAME:
            return channel["name"]
        elif i == COLUMN_ALIAS:
            if channel["alias"]:
                return channel["alias"]
            else:
                return fake_alias(channel)
        elif i == COLUMN_SUBSCRIBED:
            return channel["subscribed"]
        elif i == COLUMN_ICON:
            return rcd_util.get_channel_icon(channel["id"], 28, 28)
        elif i == COLUMN_DESCRIPTION:
            return channel["description"]

    ###
    ### GenericTreeModel implementation
    ###

    def on_get_flags(self):
        return 0

    def on_get_n_columns(self):
        return COLUMN_LAST

    def on_get_column_type(self, index):
        if index == COLUMN_ICON:
            return gtk.gdk.Pixbuf
        elif index == COLUMN_SUBSCRIBED:
            return gobject.TYPE_BOOLEAN
        else:
            return gobject.TYPE_STRING

    def on_get_path(self, node):
        return node

    def on_get_iter(self, path):
        return path

    def on_get_value(self, node, column):
        channel = self.channels[node[0]]
        if channel:
            return self.channel_to_column(channel, column)
        return "?no channel"

    def on_iter_next(self, node):
        next = node[0] + 1
        if next >= len(self.channels):
            return None
        return (next,)

    def on_iter_children(self, node):
        if node == None:
            return (0,)
        else:
            return None

    def on_iter_has_child(self, node):
        return 0

    def on_iter_nth_child(self, node, n):
        if node == None and n == 0:
            return (0,)
        else:
            return None

    def on_iter_parent(self, node):
        return None

    ###
    ### GenericTreeModel helpers
    ###

    def changed_channel(self, channel):
        i = self.channels.index(channel)
        path = (i, )
        iter = self.get_iter(path)
        self.row_changed(path, iter)

    ###
    ### Other methods
    ###

    def set_subscribed(self, channel, flag):
        if channel["subscribed"] ^ flag:
            server = rcd_util.get_server()

            if not server.rcd.users.has_privilege("subscribe"):
                # User does not have privileges to (un)subscribe
                return
            
            channel["subscribed"] = (flag and 1) or 0
            if flag:
                server.rcd.packsys.subscribe(channel["id"])
            else:
                server.rcd.packsys.unsubscribe(channel["id"])
            self.changed_channel(channel)
            # Restart the polling, w/ the first poll right now,
            # to trigger a serverlistener channels_changed event.
            red_serverlistener.reset_polling()

    def toggle_subscribed(self, channel):
        self.set_subscribed(channel, not channel["subscribed"])



def make_channel_view(model):

    view = gtk.TreeView(model)

    def toggle_cb(cr, path, model):
        channel = model.channels[int(path)]
        model.toggle_subscribed(channel)

    toggle = gtk.CellRendererToggle()
    toggle.set_property("activatable", 1)
    col = gtk.TreeViewColumn("Sub'd",
                             toggle,
                             active=COLUMN_SUBSCRIBED)
    toggle.connect("toggled", toggle_cb, model)
    view.append_column(col)

    col = gtk.TreeViewColumn()
    col.set_title("Channel")
    r1 = gtk.CellRendererPixbuf()
    r2 = gtk.CellRendererText()
    col.pack_start(r1, 0)
    col.pack_start(r2, 0)
    col.set_attributes(r1, pixbuf=COLUMN_ICON)
    col.set_attributes(r2, text=COLUMN_NAME)
    view.append_column(col)

    return view



