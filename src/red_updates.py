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
import red_packagearray, red_packageview, red_packagebrowser, red_packagebook
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

        browser = red_packagebrowser.PackageBrowser()

        view = browser.get_view()
        view.append_action_column()
        view.append_importance_column()
        view.append_channel_column(show_channel_name=0)
        view.append_name_column()
        view.append_version_column(column_title="New Version")
        view.append_current_version_column()
        view.append_size_column()
        view.set_model(self.array)

        browser.show()

        self.display("main", browser)

        lower = gtk.HBox(0, 0)
        sel = gtk.Button("Select All")
        unsel = gtk.Button("Unselect All")
        go = gtk.Button("Update All Now!")

        def sel_all_cb(b, summary):
            for pkg in summary.array.get_all():
                red_pendingops.set_action(pkg, red_pendingops.TO_BE_INSTALLED)

        def unsel_all_cb(b, summary):
            for pkg in summary.array.get_all():
                red_pendingops.set_action(pkg, red_pendingops.NO_ACTION)

        def go_cb(b, summary):
            sel_all_cb(b, summary)

        sel.connect("clicked", sel_all_cb, self)
        unsel.connect("clicked", unsel_all_cb, self)
        go.connect("clicked", go_cb, self)

        lower.pack_start(sel, 0, 0, 2)
        lower.pack_start(unsel, 0, 0, 2)
        lower.pack_end(go, 0, 0, 2)
        lower.show_all()
        self.display("lower", lower)

    def changed_visibility(self, flag):
        if flag:
            self.array.thaw()
        else:
            self.array.freeze()
        
