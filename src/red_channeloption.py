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

import rcd_util, gobject, gtk
import red_serverlistener
import string
from red_gettext import _

MATCH_ANY_CHANNEL      = -1
MATCH_NO_CHANNEL       = -2
MATCH_ANY_SUBD_CHANNEL = -3

class ChannelOption(gtk.OptionMenu, red_serverlistener.ServerListener):

    def __init__(self,
                 allow_any_channel=0,
                 allow_any_subd_channel=0,
                 allow_no_channel=0):
        gobject.GObject.__init__(self)
        red_serverlistener.ServerListener.__init__(self)
        self.__allow_any_channel=allow_any_channel
        self.__allow_any_subd_channel=allow_any_subd_channel
        self.__allow_no_channel=allow_no_channel
        self.__assemble()
        self.__last_id = None

    def __assemble(self):
        self.item_id_list = []
        menu = gtk.Menu()

        channels = rcd_util.get_all_channels()
        channels.sort(lambda x,y:cmp(string.lower(x["name"]),
                                     string.lower(y["name"])))

        if self.__allow_any_channel:
            channels.insert(0, {"name": _("All Channels"),
                                "id": MATCH_ANY_CHANNEL})

        if self.__allow_any_subd_channel:
            channels.insert(0,
                            {"name": _("All Subscribed Channels"),
                             "id": MATCH_ANY_SUBD_CHANNEL})

        if self.__allow_no_channel:
            channels.append({"name": _("No Channel"),
                             "id": MATCH_NO_CHANNEL})
        
        for c in channels:
            hbox = gtk.HBox(0, 0)

            pixbuf = rcd_util.get_channel_icon(c["id"], 24, 24)
                
            img = gtk.Image()
            img.set_size_request(24, 24)
            if pixbuf:
                img.set_from_pixbuf(pixbuf)

            label = gtk.Label(c["name"])

            hbox.pack_start(img, 0, 0, 0)
            hbox.pack_start(label, 0, 0, 4)

            item = gtk.MenuItem()
            item.add(hbox)
            item.show_all()

            self.item_id_list.append(c["id"])

            def activate_cb(item, id, opt):
                if id != self.__last_id:
                    opt.__last_id = id
                    opt.emit("selected", id)
            item.connect("activate", activate_cb, c["id"], self)
            
            menu.append(item)

        menu.show()
        self.set_menu(menu)


    def get_channel(self):
        h = self.get_history()

        if h < 0:
            return None

        id = self.item_id_list[h]
        return rcd_util.get_channel(id)

    def get_channel_id(self):
        h = self.get_history()
        if h < 0:
            return None
        return self.item_id_list[h]

    def set_channel_by_id(self, id):
        if not id in self.item_id_list:
            print "Unknown channel '%d'" % id
            assert 0

        i = self.item_id_list.index(id)
        self.set_history(i)

    def channels_changed(self):
        id = self.get_channel_id()
        self.__assemble()
        if id is not None and id in self.item_id_list:
            self.set_channel_by_id(id)
                
        
        
gobject.type_register(ChannelOption)

gobject.signal_new("selected",
                   ChannelOption,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_INT, ))
