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

class SummaryComponent(red_component.Component):

    def name(self):
        return "Summary"

    def pixbuf(self):
        return "summary"

    def get_updates(self):
        self.updates = self.server().rcd.packsys.get_updates()
        self.packages = map(lambda x:x[1], self.updates)


    def build(self):
        self.get_updates()
        self.array = red_packagearray.PackageStore()
        self.array.set(self.packages)

        ### Upper
        
        vbox = gtk.VBox(0,0)

        msg1 = gtk.Label("")
        msg1.set_markup("There are "
                        "<b>%d updates</b>"
                        " available for your system." % len (self.packages))
        vbox.pack_start(msg1, 1, 1, 0)
        
        vbox.show_all()
        self.display("upper", vbox)


        ### Main

        if self.packages:
            ex = red_explodedview.ExplodedView(array=self.array,
                                               by_importance=1)
            
            self.display("main", ex)


        ### Lower
            
        img = red_pixbuf.get_widget("update-now")
        b = gtk.Button()
        b.set_relief(gtk.RELIEF_NONE)
        b.add(img)

        box = gtk.HBox(0, 0)
        box.pack_end(b, 0, 0, 0)
        box.show_all()

        def not_yet(b):
            dialog = gtk.MessageDialog(None, 0,
                                       gtk.MESSAGE_ERROR,
                                       gtk.BUTTONS_CLOSE,
                                       "Sorry, not yet!")
            dialog.connect("response",
                           lambda b, x, d: d.destroy(),
                           dialog)
            dialog.show_all()


        b.connect("clicked", not_yet)
        
        self.display("lower", box)
        
