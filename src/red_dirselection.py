###
### Copyright (C) 2003 Ximian, Inc.
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

import os.path, gtk
from red_gettext import _

DIR_COLUMN = 0

def selection_dir_changed(tree_sel, dirsel):
    def changed_cb(model, path, iter, new_names):
        # This is probably very, very bad because we're relying on some
        # strange GTK behavior which might very well be a bug.  That is,
        # if no file is selected and nothing is in the entry, it returns
        # the current directory.
        current_dir = dirsel.get_filename()
        file = model.get_value(iter, DIR_COLUMN)
        path = os.path.abspath(current_dir + os.sep + file)
        new_names.append(path)

    new_names = []
    tree_sel.selected_foreach(changed_cb, new_names)
    dirsel.selected_dirs = new_names

class DirSelection(gtk.FileSelection):

    def __init__(self, title=""):
        gtk.FileSelection.__init__(self, title)
        self.selected_dirs = []
        
        self.dselect = self.dir_list.get_selection()
        self.dselect.set_mode(gtk.SELECTION_MULTIPLE)
        self.dselect.connect("changed", selection_dir_changed, self)

        self.file_list.parent.hide()

    def set_select_multiple(self, enabled):
        if enabled:
            self.dselect.set_mode(gtk.SELECTION_MULTIPLE)
        else:
            self.dselect.set_mode(gtk.SELECTION_SINGLE)

    def get_selections(self):
        dirs = self.selected_dirs

        entry_text = self.selection_entry.get_text()
        if entry_text:
            if os.path.isabs(entry_text):
                entry_path = entry_text
            else:
                entry_path = self.get_filename()

            if not entry_path in dirs:
                dirs.append(entry_path)
        else:
            if not dirs:
                dirs.append(self.get_filename())

        return dirs
