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
import gobject, gtk
import red_menubar

class SearchBar(gtk.HBox):

    def __init__(self):
        gobject.GObject.__init__(self)
        self.match_anyall = "all"
        self.match_substr = "substr"
        self.search_desc = 1
        self.__assemble()
        
    def __emit_search(self):
        self.emit("search",
                  self.get_match_anyall(),
                  self.get_match_word(),
                  self.get_search_descriptions(),
                  self.get_search_text())

    def get_match_anyall(self):
        return self.match_anyall

    def set_match_anyall(self, x):
        assert x in ("any", "all")
        if self.match_anyall != x:
            self.match_anyall = x
            self.__emit_search()

    def get_match_word(self):
        return self.match_substr

    def set_match_word(self, x):
        assert x in ("whole", "substr")
        if self.match_substr != x:
            self.match_substr = x
            self.__emit_search()

    def get_search_descriptions(self):
        return self.search_desc

    def set_search_descriptions(self, x):
        if x ^ self.search_desc:
            self.search_desc = x
            self.__emit_search()

    def get_search_text(self):
        return self.search_entry.get_text()

    def __assemble(self):

        bar = red_menubar.MenuBar()
        bar.add("/Search", with_dropdown_arrow=1)

        bar.add("/Search/Match All Words",
                radiogroup="anyall", radiotag="all",
                radio_get=lambda: self.get_match_anyall(),
                radio_set=lambda x: self.set_match_anyall(x))
        bar.add("/Search/Match Any Word",
                radiogroup="anyall", radiotag="any")

        bar.add("/Search/Sep1", is_separator=1)

        bar.add("/Search/Match Substrings",
                radiogroup="words", radiotag="substr",
                radio_get=lambda: self.get_match_word(),
                radio_set=lambda x: self.set_match_word(x))
        bar.add("/Search/Match Whole Words",
                radiogroup="words", radiotag="whole")

        bar.add("/Search/Sep2", is_separator=1)

        bar.add("/Search/Search Descriptions",
                checked_get = lambda: self.get_search_descriptions(),
                checked_set = lambda x: self.set_search_descriptions(x))

        self.pack_start(bar, expand=0, fill=0)
        bar.show_all()

        self.search_entry = gtk.Entry()
        self.pack_start(self.search_entry, expand=1, fill=1)
        self.search_entry.connect("activate", lambda x:self.__emit_search())
        self.search_entry.show_all()

        button = gtk.Button("Find Now")
        self.pack_start(button, expand=0, fill=0)
        button.connect("clicked", lambda x:self.__emit_search())
        button.show_all()

gobject.type_register(SearchBar)
gobject.signal_new("search",
                   SearchBar,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_STRING,
                    gobject.TYPE_STRING,
                    gobject.TYPE_BOOLEAN,
                    gobject.TYPE_STRING))
