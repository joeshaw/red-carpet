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

import sys, os, string
import gobject, gtk
import red_pixbuf

class MenuBar(gtk.MenuBar):

    def __init__(self, accel_group=None):
        gobject.GObject.__init__(self)

        self.accel_group = accel_group

        self.constructed = 0
        self.pending_items = []
        self.pending_items_hash = {}
        self.user_data = None

        # Automatically construct our menu items, and refresh the items,
        # when we are realized.
        def on_realize(x):
            x.construct()
            x.refresh_items()
            
        self.connect("realize",
                     on_realize)

    def set_user_data(self, x):
        self.user_data = x
        
    def refresh_items(self):
        self.emit("refresh_items")


    def add(self, path,
            callback=None,
            with_dropdown_arrow=0,
            is_separator=0,
            visible_fn=None,
            sensitive_fn=None,
            stock=None,
            pixbuf=None,
            pixbuf_name=None,
            checked_get=None, checked_set=None,
            radiogroup=None,
            radiotag=None,
            radio_get=None,
            radio_set=None):

        if self.constructed:
            print "Can't add '%s' to an already-constructed menu bar." \
                  % path
            assert 0

        prefix, name = os.path.split(path)
        path = string.replace(path, "_", "")

        if self.pending_items_hash.has_key(path):
            print "Collision: there is already a menu item with path '%s'" \
                  % path
            assert 0

        if pixbuf_name:
            assert not pixbuf
            pixbuf = red_pixbuf.get_pixbuf(pixbuf_name)

        item = {"path":path,
                "name":name,
                "callback":callback,
                "with_dropdown_arrow":with_dropdown_arrow,
                "is_separator":is_separator,
                "visible_fn":visible_fn,
                "sensitive_fn":sensitive_fn,
                "stock":stock,
                "pixbuf":pixbuf,
                "checked_get":checked_get,
                "checked_set":checked_set,
                "radiogroup":radiogroup,
                "radiotag":radiotag,
                "radio_get":radio_get,
                "radio_set":radio_set,
                }

        self.pending_items.append(item)
        self.pending_items_hash[path] = item

    def construct(self):

        # We can only be constructed once.
        if self.constructed:
            return
        self.constructed = 1

        tree_structure = {}
        radiogroups = {}
        
        for item in self.pending_items:
            prefix, base = os.path.split(item["path"])
            if tree_structure.has_key(prefix):
                tree_structure[prefix].append(base)
            else:
                tree_structure[prefix] = [base]

        def walk_tree(prefix, parent_menu):

            for name in tree_structure[prefix]:

                path = os.path.join(prefix, name)
                item = self.pending_items_hash[path]

                needs_refresh = item["visible_fn"] or \
                                item["sensitive_fn"]

                is_leaf = not tree_structure.has_key(path)

                item_name = item["name"] or ""

                ### Flag items that aren't hooked up to callbacks.
                if is_leaf and not item["callback"]:
                    item_name = item_name + " (inactive)"

                if item["is_separator"]:
                    menu_item = gtk.SeparatorMenuItem()
                    
                elif item["stock"]:
                    menu_item = gtk.ImageMenuItem(item["stock"],
                                                  self.accel_group)
                elif item["pixbuf"]:
                    menu_item = gtk.ImageMenuItem()
                    menu_item.set_image(item["pixbuf"])
                elif item["radiogroup"] and item["radiotag"]:

                    grp = radiogroups.get(item["radiogroup"])
                    grp_widget = None
                    if grp:
                        grp_widget, grp_item = grp
                        item["radio_get"] = grp_item["radio_get"]
                        item["radio_set"] = grp_item["radio_set"]
                        
                    
                    menu_item = gtk.RadioMenuItem(grp_widget, item["name"])
                    if not grp:
                        #assert item["radio_get"] and item["radio_set"]
                        radiogroups[item["radiogroup"]] = (menu_item,
                                                           item)

                    def radio_activate(mi, get_fn, set_fn, tag):
                        print "activate", get_fn(), tag
                        if get_fn() != tag:
                            set_fn(tag)

                    menu_item.connect_after("activate",
                                            radio_activate,
                                            item["radio_get"],
                                            item["radio_set"],
                                            item["radiotag"])

                    needs_refresh = 1
                    
                elif item["checked_get"] and item["checked_set"]:
                    menu_item = gtk.CheckMenuItem(item["name"])
                    menu_item.set_active(item["checked_get"]())
                    needs_refresh = 1
                    
                    def check_activate(mi, get_fn, set_fn):
                        state = mi.get_active()
                        x = (get_fn() and 1) or 0
                        if x ^ state:
                            set_fn(state)
                            
                    menu_item.connect_after("activate",
                                            check_activate,
                                            item["checked_get"],
                                            item["checked_set"])
                else:
                    if item["with_dropdown_arrow"]:
                        menu_item = gtk.MenuItem()
                        hbox = gtk.HBox(0, 0)
                        hbox.pack_start(gtk.Label(item_name), 0, 0, 0)
                        hbox.pack_start(gtk.Arrow(gtk.ARROW_DOWN,
                                                  gtk.SHADOW_OUT), 0, 0, 0)
                        menu_item.add(hbox)
                    else:
                        menu_item = gtk.MenuItem(item_name)

                parent_menu.append(menu_item)
                menu_item.show_all()

                ### If this item is a leaf in our tree,
                ### hook up it's callback

                if is_leaf and item["callback"]:
                    menu_item.connect_after(
                        "activate",
                        lambda x, i:i["callback"](self.user_data),
                        item)

                ###
                ### If this item has special visibility, sensitivity or checked
                ### functions, hook them up to listen for our refresh_items
                ### signals.
                ###

                def refresh_items(widget, item):
                    visible_fn = item["visible_fn"]
                    if (not visible_fn) or visible_fn():
                        widget.show()
                    else:
                        widget.hide()
                    
                    sensitive_fn = item["sensitive_fn"]
                    widget.set_sensitive((not sensitive_fn) or sensitive_fn())

                    checked_get = item["checked_get"]
                    if checked_get:
                        x = (checked_get() and 1) or 0
                        widget.set_active(x)

                    radiogroup = item["radiogroup"]
                    radiotag = item["radiotag"]
                    radio_get = item["radio_get"]
                    radio_set = item["radio_set"]
                    if radiogroup and radiotag and radio_get and radio_set:
                        active_tag = radio_get()
                        print radiotag, active_tag
                        widget.set_active(radiotag == active_tag)

                if needs_refresh:
                    self.connect("refresh_items",
                                 lambda menu, x, y: refresh_items(x, y),
                                 menu_item, item)

                ###
                ### If this item has subitems, construct the submenu
                ### and continue walking down the tree.
                ###

                if not is_leaf:

                    # Refresh the menu bar every time a top-level
                    # menu item is opened.
                    if prefix == "/":
                        menu_item.connect("activate",
                                          lambda x:self.refresh_items())
                    submenu = gtk.Menu()
                    menu_item.set_submenu(submenu)
                    submenu.show()
                    walk_tree(path, submenu)

        walk_tree("/", self)

gobject.type_register(MenuBar)


gobject.signal_new("refresh_items",
                   MenuBar,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   ())
