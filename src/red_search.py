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
import gtk
import rcd_util
import red_header, red_pixbuf
import red_packagearray, red_channeloption, red_explodedview
import red_component

class SearchComponent(red_component.Component):

    def name(self):
        return "Search"

    def pixbuf(self):
        return "info-button"

    def build(self):
        self.array = red_packagearray.PackagesFromQuery(self.server())

        ### Upper

        hbox = gtk.HBox(0,0)
        msg = gtk.Label("Search:")
        hbox.pack_start(msg, 0, 0, 0)

        self.search_data = gtk.Entry()
        hbox.pack_start(self.search_data, 1, 1, 0)

        button = gtk.Button("_Search")
        hbox.pack_start(button, 0, 0, 0)

        self.array.set_query([])
        self.search_data.connect("activate", lambda x:self.array.set_query([["name", "contains", self.search_data.get_text()]]))
        button.connect("clicked", lambda x:self.array.set_query([["name", "contains", self.search_data.get_text()]]))
        
        hbox.show_all()
        self.display("upper", hbox)


        ### Main

        if self.array.len() > 0:
            ex = red_explodedview.ExplodedView(array=self.array,
                                               by_channel=1)
            
            self.display("main", ex)

    def changed_visibility(self, flag):
        if flag:
            self.array.thaw()
        else:
            self.array.freeze()
        
