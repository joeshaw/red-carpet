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

import sys, string
import ximian_xmlrpclib, rcd_util
import gobject, gtk
import red_pixbuf

colcounter = -1
def next_col():
    global colcounter
    colcounter = colcounter + 1
    return colcounter

COLUMN_NAME       = next_col()
COLUMN_ICON       = next_col()
COLUMN_ICON_SMALL = next_col()
COLUMN_SUBSCRIBED = next_col()
COLUMN_BUTTON     = next_col()
COLUMN_LAST       = next_col()


class SubscriptionModel(gtk.GenericTreeModel):

    def __init__(self):
        self.channels = rcd_util.get_all_channels()
        gtk.GenericTreeModel.__init__(self)

    def on_get_flags(self):
        return 0

    def on_get_n_columns(self):
        return COLUMN_LAST

    def on_get_column_type(self, i):
        if i == COLUMN_NAME:
            return gobject.TYPE_STRING
        elif i == COLUMN_ICON:
            return gtk.gdk.Pixbuf.__gtype__
        elif i == COLUMN_SUBSCRIBED:
            return gobject.TYPE_BOOLEAN
        elif i == COLUMN_BUTTON:
            return gtk.gdk.Pixbuf.__gtype__

    def on_get_path(self, node):
        return (node,)

    def on_get_iter(self, path):
        return path[0]

    def on_get_value(self, node, i):
        c = self.channels[node]
        if i == COLUMN_NAME:
            return c["name"]
        elif i == COLUMN_ICON:
            return rcd_util.get_channel_icon(c["id"])
        elif i == COLUMN_ICON_SMALL:
            return rcd_util.get_channel_icon(c["id"], 32, 32)
        elif i == COLUMN_SUBSCRIBED:
            return c["subscribed"]
        elif i == COLUMN_BUTTON:
            if c["subscribed"]:
                return red_pixbuf.get_pixbuf("subscribe")
            else:
                return red_pixbuf.get_pixbuf("unsubscribe")

    def on_iter_next(self, node):
        N = len(self.channels)
        node = node + 1
        if node < N:
            return node
        else:
            return None

    def on_iter_children(self, node):
        if node == None:
            return 0
        else:
            return None

    def on_iter_has_child(self, node):
        return 0

    def on_iter_nth_child(self, node, n):
        if node == None:
            return n
        else:
            return None

    def on_iter_parent(self, node):
        return None


class SubscriptionView(gtk.TreeView):

    def __init__(self):
        gtk.TreeView.__init__(self)
        self.construct()
        self.set_model(SubscriptionModel())

    def construct(self):

        self.icon_col = gtk.TreeViewColumn("",
                                           gtk.CellRendererPixbuf(),
                                           pixbuf=COLUMN_ICON)
        self.append_column(self.icon_col)

        self.name_col = gtk.TreeViewColumn("Name",
                                           gtk.CellRendererText(),
                                           markup=COLUMN_NAME)
        self.append_column(self.name_col)


        self.button_col = gtk.TreeViewColumn("",
                                             gtk.CellRendererPixbuf(),
                                             pixbuf=COLUMN_BUTTON)
        self.append_column(self.button_col)


        
        
