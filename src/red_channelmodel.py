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

import string
import re

import gtk
import gobject

import rcd_util
import red_listmodel
import red_serverlistener

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

class ChannelModel(red_listmodel.ListModel, red_serverlistener.ServerListener):

    def __init__(self, sort_fn=sort_channels_by_name, filter_fn=None):
        red_listmodel.ListModel.__init__(self, sort_fn, filter_fn)
        red_serverlistener.ServerListener.__init__(self)

        self.__channels = rcd_util.get_all_channels()

        for name, callback, type in COLUMNS:
            self.add_column(callback, type)

        self.refresh()

    ###
    ### red_listmodel.ListModel implementation
    ###

    def get_all(self):
        return self.__channels

    def spew(self):
        for c in self.get_all():
            print c

    ###
    ### ServerListener methods
    ###

    def channels_changed(self):
        self.refresh()

    def subscriptions_changed(self):
        self.refresh()

    def refresh(self):
        def refresh_cb(me):
            me.__channels = rcd_util.get_all_channels()
        self.changed(refresh_cb)

    ###
    ### Other methods
    ###

    def toggle_subscribed(self, channel):

        def subscribe_cb(th, model, channel, sub):
            def set_cb(m, ch, flag):
                ch["subscribed"] = (flag and 1) or 0
            model.changed(set_cb, channel, sub)
        
        server = rcd_util.get_server_proxy()

        if channel["subscribed"]:
            th = server.rcd.packsys.unsubscribe(channel["id"])
        else:
            th = server.rcd.packsys.subscribe(channel["id"])

        th.connect("ready", subscribe_cb, self, channel,
                   not channel["subscribed"])
