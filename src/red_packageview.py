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

import gobject, gtk

class PackageView(gtk.TreeView):

    def __init__(self):
        gtk.TreeView.__init__(self)
        self.changed_id = 0
        self.set_rules_hint(1)

    def thrash_model(self):
        model = self.get_model()
        gtk.TreeView.set_model(self, None)
        gtk.TreeView.set_model(self, model)

    def set_model(self, model):
        # FIXME: make sure that we are passing in a PackageArray
        # for the model.
        old_model = self.get_model()
        if self.changed_id:
            old_model.disconnect(self.changed_id)
        self.changed_id = 0

        gtk.TreeView.set_model(self, model)

        if model:
            self.changed_id = model.connect_after("changed",
                                                  lambda x:self.thrash_model())
