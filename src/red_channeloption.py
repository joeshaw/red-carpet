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

import rcd_util
import red_serverlistener
import gobject, gtk

class ChannelOption(gtk.OptionMenu, red_serverlistener.ServerListener):

    def __init__(self):
        gobject.GObject.__init__(self)
        red_serverlistener.ServerListener.__init__(self)
        self.__assemble()

    def __assemble(self):
        self.item_id_list = []
        menu = gtk.Menu()
        for c in rcd_util.get_all_channels():
            hbox = gtk.HBox(0, 0)

            pixbuf = rcd_util.get_channel_icon(c["id"], 28, 28)
            img = gtk.Image()
            img.set_from_pixbuf(pixbuf)

            label = gtk.Label("%s (%d)" % (c["name"], c["id"]))

            hbox.pack_start(img, 0, 0, 0)
            hbox.pack_start(label, 0, 0, 0)

            item = gtk.MenuItem()
            item.add(hbox)
            item.show_all()

            self.item_id_list.append(c["id"])

            item.connect("activate",
                         lambda item, id:self.emit("selected", id),
                         c["id"])
            
            menu.append(item)

        menu.show()
        self.set_menu(menu)


    def get_channel(self):
        id = self.item_id_list[self.get_history()]
        return rcd_util.get_channel(id)

    def get_channel_id(self):
        c = self.get_channel()
        if c:
            return c["id"]
        return None

    def set_channel_by_id(self, id):
        if not id in self.item_id_list:
            print "Unknown channel '%d'" % id
            assert 0

        i = self.item_id_list.index(id)
        self.set_history(i)

    def channels_changed(self, server):
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
