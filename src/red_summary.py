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
import red_packagearray, red_packageview
import red_component

class SummaryComponent(red_component.Component):

    def name(self):
        return "Summary"

    def pixbuf(self):
        return "summary"

    def package_selected_cb(self, pkg, action):
        if action != "install":
            print "Expected an 'install' action, got '" + action + "'"
            return
        
        if pkg in self.transaction.install_packages:
            self.transaction.remove_install_package(pkg)
        else:
            self.transaction.add_install_package(pkg)

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
        view.append_importance_column()
        view.append_name_column(show_channel_icon=1)
        view.append_version_column(column_title="New Version")
        view.append_current_version_column()
        view.append_size_column()
        view.set_model(self.array)

        self.display("main", view)

    def changed_visibility(self, flag):
        if flag:
            self.array.thaw()
        else:
            self.array.freeze()
        
