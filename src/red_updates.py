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

import gtk
import red_packagearray, red_packagebrowser
import red_pendingops
import red_component
import rcd_util

class SummaryComponent(red_component.Component):

    def name(self):
        return "Summary"

    def long_name(self):
        return "Update Summary"

    def pixbuf(self):
        return "summary"

    def accelerator(self):
        return "<Control>s"

    def show_on_toolbar(self):
        return 1

    def build(self):
        self.array = red_packagearray.UpdatedPackages()

        page = gtk.VBox(0, 0)

        vbox = gtk.VBox(0,0)

        def updates_changed_cb(array, label):
            if array.len() == 0:
                markup = "Your system is up to date."
            else:
                markup = "There are <b>%d updates</b>" \
                         " available for your system." % array.len()
                
            label.set_markup(markup)

        msg1 = gtk.Label("")
        self.array.connect("changed", updates_changed_cb, msg1)
        vbox.pack_start(msg1, 1, 1, 0)

        vbox.show_all()
        
        page.pack_start(vbox, 0, 0)

        ### Main

        browser = red_packagebrowser.PackageBrowser()

        view = browser.get_view()
        view.append_action_column()
        col = view.append_importance_column()
        view.append_channel_column()
        view.append_name_column()
        view.append_version_column(column_title="New Version")
        view.append_current_version_column()
        view.set_model(self.array)

        view.sort_by(col)

        browser.show()

        page.pack_start(browser, 1, 1)

        return page


    def changed_visibility(self, flag):
        if flag:
            self.array.thaw()
        else:
            self.array.freeze()

    def select_all_sensitive(self):
        return rcd_util.check_server_permission("upgrade")

    def select_all(self):
        for pkg in self.array.get_all():
            red_pendingops.set_action(pkg, red_pendingops.TO_BE_INSTALLED)

    def unselect_all(self):
        for pkg in self.array.get_all():
            red_pendingops.set_action(pkg, red_pendingops.NO_ACTION)
