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
import red_packagearray, red_packageview, red_packagebook
import red_pendingops
import red_component

class SummaryComponent(red_component.Component):

    def name(self):
        return "Summary"

    def pixbuf(self):
        return "summary"

    def build(self):
        self.array = red_packagearray.UpdatedPackages()

        ### Upper
        
        vbox = gtk.VBox(0,0)

        msg1 = gtk.Label("")
        msg1.set_markup("There are "
                        "<b>%d updates</b>"
                        " available for your system." % self.array.len())
        vbox.pack_start(msg1, 1, 1, 0)
        
        vbox.show_all()
        self.display("upper", vbox)


        ### Main

        view = red_packageview.PackageView()
        view.append_action_column()
        view.append_importance_column()
        view.append_channel_column(show_channel_name=0)
        view.append_name_column()
        view.append_version_column(column_title="New Version")
        view.append_current_version_column()
        view.append_size_column()
        view.set_model(self.array)

        self.display("main", view)

        def act_cb(view, i, pkg):
            red_pendingops.toggle_action(pkg)
            view.get_model().row_changed(i)

        view.connect("activated", act_cb)

    def changed_visibility(self, flag):
        if flag:
            self.array.thaw()
        else:
            self.array.freeze()
        
