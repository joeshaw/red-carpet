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

_status_types = (
    ("Uninstalled", lambda p: not p["installed"] and not p["name_installed"]),
    ("Upgrade",     lambda p: p["name_installed"] > 0),
    ("Installed",   lambda p: p["installed"] or p["name_installed"]),
    ("All",         lambda p: 1),
    )

class StatusOption(gtk.OptionMenu):

    def __init__(self):
        gtk.OptionMenu.__init__(self)
        self.__current_filter = _status_types[0][1] # the default setting

        menu = gtk.Menu()

        for text, filter_fn in _status_types:
            item = gtk.MenuItem(text)
            item.show_all()
            menu.append(item)

            def activate_cb(item, opt, fn):
                opt.__current_filter = fn
            item.connect("activate", activate_cb, self, filter_fn)

        menu.show()
        self.set_menu(menu)

    def get_current_filter(self):
        return self.__current_filter
        

