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
import re

import gtk
import gobject

import rcd_util
import red_extra
import red_serverlistener
import red_thrashingtreeview

def get_alias(ch):
    if ch["alias"]:
        return ch["alias"]
    else:
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

COLUMNS = (
    ("CHANNEL",
     lambda x:x,
     gobject.TYPE_PYOBJECT),
    
    ("ID",
     lambda x:x["id"],
     gobject.TYPE_INT),
    
    ("NAME",
     lambda x:x["name"],
     gobject.TYPE_STRING),
    
    ("ALIAS",
     lambda x:get_alias(x),
     gobject.TYPE_STRING),
    
    ("SUBSCRIBED",
     lambda x:x["subscribed"],
     gobject.TYPE_BOOLEAN),

    ("TRANSIENT",
     lambda x:x["transient"],
     gobject.TYPE_BOOLEAN),
    
    ("ICON",
     lambda x:rcd_util.get_channel_icon(x["id"], 28, 28),
     gtk.gdk.Pixbuf),
    
    ("DESCRIPTION",
     lambda x:x["description"],
     gobject.TYPE_STRING),
    )

for i in range(len(COLUMNS)):
    name = COLUMNS[i][0]
    exec("COLUMN_%s = %d" % (name, i))

def sort_channels_by_name(a,b):
    return cmp(string.lower(a["name"]), string.lower(b["name"]))

class ChannelModel(red_extra.ListModel, red_serverlistener.ServerListener):

    def __init__(self, sort_fn=None, filter_fn=None):
        gobject.GObject.__init__(self)
        red_serverlistener.ServerListener.__init__(self)
        self.__pending_changes = []
        self.__sort_fn = sort_fn
        if sort_fn is None:
            self.__sort_fn = sort_channels_by_name
        self.__reverse_sort = 0
        self.__filter_fn = filter_fn
        self.__channels = rcd_util.get_all_channels()

        self.set_list(self.__channels)
        self.set_sort_magic(self.__sort_fn, self.__reverse_sort)
        self.set_filter_magic(self.__filter_fn)

        for name, callback, type in COLUMNS:
            self.add_column(callback, type)

    ###
    ### red_extra.ListModel implementation
    ###

    def len(self):
        all = self.get_all()
        return len(all)

    def get(self, i):
        all = self.get_all()
        return all[i]

    def get_all(self):
        return self.__channels

    def spew(self):
        for c in self.get_all():
            print c

    ###
    ### ServerListener methods
    ###

    def channels_changed(self):
        print "Channels changed!"
        self.refresh()

    def subscriptions_changed(self):
        print "Subscriptions changed!"
        self.refresh()

    def refresh(self):
        print "refreshing channels"
        def refresh_cb(me):
            me.__channels = rcd_util.get_all_channels()
        self.changed(refresh_cb)

    ###
    ### Other methods
    ###

    def do_changed(self):
        operator, args = self.__pending_changes.pop()
        if operator:
            apply(operator, (self,) + args)

            self.set_list(self.get_all())
            self.set_sort_magic(self.__sort_fn, self.__reverse_sort)
            self.set_filter_magic(self.__filter_fn)
            
    def changed(self, operator, *args):
        self.__pending_changes.append((operator, args))
        self.emit("changed")

    def toggle_subscribed(self, channel):
        def set_subscribed_fn(model, ch, flag):
            server = rcd_util.get_server()

            ch["subscribed"] = (flag and 1) or 0

            if flag:
                server.rcd.packsys.subscribe(ch["id"])
            else:
                server.rcd.packsys.unsubscribe(ch["id"])

        self.changed(set_subscribed_fn, channel, not channel["subscribed"])

gobject.type_register(ChannelModel)

gobject.signal_new("changed",
                   ChannelModel,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   ())


def make_channel_view(model):

    view = red_thrashingtreeview.TreeView(model)

    def toggle_cb(cr, path, model):
        c = model.get_list_item(int(path))
        model.toggle_subscribed(c)

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



