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

import gobject, gtk
import red_pixbuf

section_table = ( ("Any Section",               None,         -1),
                  ("Productivity Applications", "office",      0),
                  ("Imaging",                   "imaging",     1),
                  ("Personal Information Mgmt", "pim",         2),
                  ("X Windows Applications",    "xapp",        3),
                  ("Games",                     "game",        4),
                  ("Multimedia",                "multimedia",  5),
                  ("Internet",                  "internet",    6),
                  ("Utilities",                 "util",        7),
                  ("System",                    "system",      8),
                  ("Documentation",             "doc",         9),
                  ("Libraries",                 "library",    10),
                  ("Development",               "devel",      11),
                  ("Development Utilities",     "develutil",  12),
                  ("Miscellaneous",             "misc",       13),
                  )

class SectionOption(gtk.OptionMenu):

    def __init__(self, array=None):
        gobject.GObject.__init__(self)
        self.item_num_list = []
        self.array = None
        self.array_changed = 0
        self.current_selection = -1

        if array:
            self.set_array(array)

    def assemble_menu(self):
        sections = [("All", None, -1)]

        if self.array:
            seen_sections = {}
            for pkg in self.array.get_all():
                num = pkg["section_num"]
                if not seen_sections.has_key(num):
                    sections.append((pkg["section_user_str"],
                                     "section-" + pkg["section_str"],
                                     num))
                    seen_sections[num] = 1

        sections.sort(lambda a, b: cmp(a[2], b[2]))

        self.item_num_list = []

        menu = gtk.Menu()
        for name, icon, num in sections:
            hbox = gtk.HBox(0, 0)

            if icon:
                img = red_pixbuf.get_widget(icon, width=24, height=24)
                hbox.pack_start(img, 0, 0, 0)

            label = gtk.Label(name)
            hbox.pack_start(label, 0, 0, 4)

            item = gtk.MenuItem()
            item.add(hbox)
            item.show_all()

            self.item_num_list.append(num)

            def activate_cb(item, id, this):
                if this.current_selection != id:
                    this.emit("selected", id)
                    this.current_selection = id

            item.connect("activate", activate_cb, num, self)

            menu.append(item)

        menu.show()
        self.set_menu(menu)

        # Restore selection if necessary.
        if self.current_selection >= 0:
            self.set_history(self.item_num_list.index(self.current_selection))

    def set_array(self, array):
        if self.array_changed:
            self.array.disconnect(self.array_changed)
            self.array_changed = 0
    
        self.array = array

        if array:
            def changed_cb(array, optmenu):
                optmenu.assemble_menu()
            self.array_changed = self.array.connect_after("changed",
                                                          changed_cb,
                                                          self)
            self.assemble_menu()

    def get_section_num(self):
        return self.item_num_list[self.get_history()]


gobject.type_register(SectionOption)

gobject.signal_new("selected",
                   SectionOption,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_INT, ))
