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

import string, gobject, gtk
import rcd_util, red_pixbuf
import red_channeloption, red_settings

from red_gettext import _

MATCH_ANY_WORD    = 0
MATCH_ALL_WORDS   = 1
MATCH_WHOLE_WORDS = 0
MATCH_SUBSTRINGS  = 1

class _ShowAdvanced(gobject.GObject):

    conf_str = "UI/show_advanced_search_options"

    def __init__(self):
        gobject.GObject.__init__(self)
        config = red_settings.get_config()
        self.__show = int(config.get(self.conf_str + "=0"))

    def set(self, x):
        if self.__show ^ x:
            self.__show = x
            config = red_settings.get_config()
            config.set(self.conf_str, x)
            config.sync()
            self.emit("changed", x)

    def get(self):
        return self.__show

gobject.type_register(_ShowAdvanced)
gobject.signal_new("changed",
                   _ShowAdvanced,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_INT,))

_showadv = _ShowAdvanced()

def show_advanced_get():
    return _showadv.get()

def show_advanced_set(x):
    _showadv.set(x)
    


class SearchBox(gtk.VBox):

    def __init__(self,
                 allow_entry=1,
                 allow_advanced=1,
                 system_packages_only=0,
                 uninstalled_packages_only=0):
        gobject.GObject.__init__(self)

        # system packages and uninstalled packages are mutually exclusive
        assert (system_packages_only and uninstalled_packages_only) == 0

        self.__allow_entry               = allow_entry
        self.__allow_advanced            = allow_advanced
        self.__system_packages_only      = system_packages_only
        self.__uninstalled_packages_only = uninstalled_packages_only

        self.__pending_change = 0

        self.__last_query         = None
        self.__last_status_filter = None
        self.__last_section       = None

        self.__widget_box = None

        self.__assemble()


    def set_widget(self, w):
        self.__widget_box.add(w)


    def __emit(self):
        query = self.get_query()
        filter_fn = self.get_filter
        cid = self.__ch_opt.get_channel_id()

        if query != self.__last_query \
               or self.__match_section != self.__last_section \
               or self.__status_filter != self.__last_status_filter \
               or self.__last_cid != cid:
            self.__last_query = query
            self.__last_section = self.__match_section
            self.__last_status_filter = self.__status_filter
            self.__last_cid = cid
            self.emit("search", query, filter_fn)

        self.__pending_change = 0
        return 0


    def __changed(self, lag=0):
        
        if self.__pending_change:
            gtk.timeout_remove(self.__pending_change)
            self.__pending_change = 0
            
        if lag <= 0:
            self.__emit()
        else:
            self.__pending_change = gtk.timeout_add(lag,
                                                    lambda x: x.__emit(),
                                                    self)


    def __assemble_status_option(self):

        def uninstalled_cb(p):
            return not p["installed"] and not p["name_installed"]

        def update_cb(p):
            return p["name_installed"] > 0 and not p["installed"]

        def installed_cb(p):
            return p["installed"] or p["name_installed"]

        def all_cb(p):
            return 1
        
        status_types = (
            (_("All Packages"),          all_cb),
            (_("Updates"),               update_cb),
            (_("Uninstalled Packages"),  uninstalled_cb),
            (_("Installed Packages"),    installed_cb),
            )


        menu = gtk.Menu()
        for name, filter_fn in status_types:
            mi = gtk.MenuItem(name)
            def set_cb(x, sbox, fn):
                sbox.__status_filter = fn
                sbox.__changed()
            mi.connect("activate", set_cb, self, filter_fn)
            mi.show()
            menu.append(mi)
        menu.show()

        opt = gtk.OptionMenu()
        opt.set_menu(menu)

        self.__status_filter = all_cb

        return opt


    def __assemble_section_option(self):

        section_table = ( (_("All Sections"),        None,          -1),
                          (_("Productivity"),        "office",       0),
                          (_("Imaging"),             "imaging",      1),
                          (_("Personal Info. Mgmt"), "pim",          2),
                          (_("X Windows"),           "xapp",         3),
                          (_("Games"),               "game",         4),
                          (_("Multimedia"),          "multimedia",   5),
                          (_("Internet"),            "internet",     6),
                          (_("Utilities"),           "util",         7),
                          (_("System"),              "system",       8),
                          (_("Documentation"),       "doc",          9),
                          (_("Libraries"),           "library",     10),
                          (_("Development"),         "devel",       11),
                          (_("Development Tools"),   "develutil",   12),
                          (_("Miscellaneous"),       "misc",        13),
                          )

        menu = gtk.Menu()
        width, height = gtk.icon_size_lookup(gtk.ICON_SIZE_MENU)
        for name, icon, code in section_table:
            hbox = gtk.HBox(0, 0)

            if icon:
                icon = "section-" + icon
                img = red_pixbuf.get_widget(icon, width=width, height=height)
                hbox.pack_start(img, expand=0, fill=0, padding=0)

            label = gtk.Label(name)
            hbox.pack_start(label, expand=0, fill=0, padding=4)

            mi = gtk.MenuItem()
            def set_cb(x, sbox, code):
                sbox.__match_section = code
                self.__changed()
            mi.connect("activate", set_cb, self, code)
            mi.add(hbox)
            mi.show_all()

            menu.append(mi)

        opt = gtk.OptionMenu()
        opt.set_menu(menu)

        self.__match_section = -1

        return opt


    def __assemble_any_or_all_option_menu(self):

        table = ( ("Any Word",  MATCH_ANY_WORD),
                  ("All Words", MATCH_ALL_WORDS),
                  )

        menu = gtk.Menu()
        for name, code in table:
            mi = gtk.MenuItem(name)
            def set_cb(x, sbox, code):
                sbox.__match_any_or_all = code
                sbox.__changed()
            mi.connect("activate", set_cb, self, code)
            mi.show()
            menu.append(mi)

        opt = gtk.OptionMenu()
        opt.set_menu(menu)

        self.__match_any_or_all = MATCH_ANY_WORD

        return opt


    def __assemble_whole_or_substr_option_menu(self):

        table = ( ("Substrings",  MATCH_SUBSTRINGS),
                  ("Whole Words", MATCH_WHOLE_WORDS),
                  )

        menu = gtk.Menu()
        for name, code in table:
            mi = gtk.MenuItem(name)
            def set_cb(x, sbox, code):
                sbox.__match_whole_or_substr = code
                sbox.__changed()
            mi.connect("activate", set_cb, self, code)
            mi.show()
            menu.append(mi)

        opt = gtk.OptionMenu()
        opt.set_menu(menu)

        self.__match_whole_or_substr = MATCH_SUBSTRINGS

        return opt
            

    def __assemble_advanced(self):

        adv_row = gtk.HBox(0, 0)

        desc_b = gtk.CheckButton(_("Search descriptions"))
        desc_b.set_active(1)
        adv_row.pack_start(desc_b, expand=0, fill=0, padding=0)

        desc_b.connect("toggled", lambda b, sbox: sbox.__changed(), self)

        self.__search_desc = desc_b

        ###
        ### Match radio buttons
        ###

        match_label = gtk.Label(_("Match:"))

        any_all = self.__assemble_any_or_all_option_menu()
        whole_substr = self.__assemble_whole_or_substr_option_menu()

        match_box = gtk.HBox(0, 0)
        match_box.pack_start(match_label, padding=2)
        match_box.pack_start(any_all)
        match_box.pack_start(gtk.VSeparator(), padding=5)
        match_box.pack_start(whole_substr)
        match_box.show_all()

        adv_row.pack_end(match_box, expand=0, fill=0, padding=0)

        adv_row.show_all()
        adv_row.hide()
        if show_advanced_get():
            adv_row.show()

        def showadv_cb(sa, flag, w):
            if flag:
                w.show()
            else:
                w.hide()
            
        _showadv.connect("changed", showadv_cb, adv_row)
            
        return adv_row



    def __assemble(self):

        top_row = gtk.HBox(0, 0)

        channel_label = gtk.Label("")
        channel_label.set_markup(_("Channel:"))
        top_row.pack_start(channel_label, expand=0, fill=0, padding=2)

        any_subd = 1
        no_chan = 1
        if self.__system_packages_only:
            any_subd=0
        elif self.__uninstalled_packages_only:
            no_chan = 0

        self.__ch_opt = red_channeloption.ChannelOption(allow_any_channel=1,
                                                        allow_any_subd_channel=any_subd,
                                                        allow_no_channel=no_chan)
        self.__ch_opt.connect("selected",
                              lambda x, y, z: z.__changed(),
                              self)
        top_row.pack_start(self.__ch_opt, expand=1, fill=1, padding=0)

        top_row.show_all()

        ###
        ### Build the second row of the search UI, which contains the
        ### entry and some option menus.
        ###

        entry_row = gtk.HBox(0, 6)

        sect_opt = self.__assemble_section_option()
        entry_row.pack_start(sect_opt, expand=0, fill=0, padding=0)

        stat_opt = self.__assemble_status_option()
        entry_row.pack_start(stat_opt, expand=0, fill=0, padding=0)

        self.__entry = gtk.Entry()
        def entry_changed_cb(e, x):
            lag = 500
            # Make the lag longer if we haven't typed much yet.
            if len(e.get_text()) < 3:
                lag *= 2
            x.__changed(lag=lag)
        self.__entry.connect("changed", entry_changed_cb, self)
        self.__entry.connect("activate",
                             lambda e, x: x.__changed(),
                             self)
        entry_row.pack_end(self.__entry, expand=1, fill=1, padding=2)

        if self.__allow_entry:
            entry_row.show_all()

        if self.__system_packages_only or self.__uninstalled_packages_only:
            stat_opt.hide()
            self.__status_filter = None


        ###
        ### Create a box for our 'view' widget.
        ###

        self.__widget_box = gtk.VBox(0, 0)
        self.__widget_box.show_all()


        ###
        ### Build our bottom row of advanced options.
        ###

        self.__adv_row = self.__assemble_advanced()

        ###
        ### Assemble all of these pieces into our VBox.

        self.pack_start(top_row, expand=0, fill=0, padding=2)
        self.pack_start(entry_row, expand=0, fill=0, padding=2)
        self.pack_start(self.__widget_box, expand=1, fill=1, padding=2)
        self.pack_start(self.__adv_row, expand=0, fill=0, padding=2)


    def try_to_grab_focus(self):
        if self.__allow_entry:
            w = self.__entry
        else:
            w = self.__ch_opt
        gtk.idle_add(lambda x: x.grab_focus(), w)


    def get_query(self):

        query = []

        search_desc = self.__search_desc.get_active()
        if search_desc:
            search_key = "text"
        else:
            search_key = "name"

        if self.__match_whole_or_substr == MATCH_SUBSTRINGS:
            search_match = "contains"
        else:
            search_match = "contains_word"

        search_text = self.__entry.get_text()
        if search_text:
            for t in string.split(search_text):
                query.append([search_key, search_match, t])

        if query and self.__match_any_or_all == MATCH_ANY_WORD:
            query.insert(0, ["", "begin-or", ""])
            query.append(["", "end-or", ""])

        if self.__system_packages_only:
            query.append(["installed", "is", "true"])
            channel_id = 0
        elif self.__uninstalled_packages_only:
            query.append(["name-installed", "is", "false"])
            channel_id = 0
        else:
            channel_id = self.__ch_opt.get_channel_id()
            if channel_id >= 0:
                query.append(["channel", "is", channel_id])

        return query
    

    def get_filter(self):

        channel_id = self.__ch_opt.get_channel_id()
        subd_dict = {}
        if channel_id == red_channeloption.MATCH_ANY_SUBD_CHANNEL:
            subd_dict[0] = 1  # We are always subscribed to channel 0
                              # (i.e. system packages)
            for c in rcd_util.get_all_channels():
                if c.get("subscribed"):
                    subd_dict[c["id"]] = 1

        def filter_fn(p,
                      n=self.__match_section,
                      status_fn=self.__status_filter,
                      subd_dict=subd_dict):

            if subd_dict and not subd_dict.has_key(p.get("channel")):
                return 0

            if channel_id == red_channeloption.MATCH_NO_CHANNEL \
                   and (p.get("channel") != 0 or p.has_key("channel_guess")):
                return 0

            # XXX - Fix these numeric comparisons!
            if self.__system_packages_only \
               and channel_id > 0 \
               and channel_id != p.get("channel_guess"):
                return 0

            if self.__uninstalled_packages_only \
               and channel_id > 0 \
               and channel_id != p.get("channel"):
                return 0
            
            sect = p.get("section_num")
            return (not status_fn or status_fn(p)) and (n < 0 or sect == n)

        return filter_fn


gobject.type_register(SearchBox)
gobject.signal_new("search",
                   SearchBox,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,  # query
                    gobject.TYPE_PYOBJECT,  # filter fn
                    ))
