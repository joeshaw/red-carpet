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
import red_menubar
import red_channeloption, red_sectionoption, red_statusoption

class SearchBar(gtk.VBox):

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

        box1 = gtk.HBox(0, 0)
        box2 = gtk.HBox(0, 0)

        ###
        ### Build the top row of the bar, where we can filter by
        ### channel, status, etc.

        box1.pack_start(gtk.Label("Foo!"), expand=0, fill=0)

        ch_opt   = red_channeloption.ChannelOption(allow_any_channel=1)
        sect_opt = red_sectionoption.SectionOption()
        stat_opt = red_statusoption.StatusOption()

        box1.pack_start(ch_opt, expand=0, fill=0)
        box1.pack_start(sect_opt, expand=0, fill=0)
        box1.pack_start(stat_opt, expand=0, fill=0)
        
        

        ###
        ### Put together second row, with the search entry and dropdown
        ### button w/ search characteristics.
        ###

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

        box2.pack_start(bar, expand=0, fill=0)

        self.search_entry = gtk.Entry()
        box2.pack_start(self.search_entry, expand=1, fill=1)
        self.search_entry.connect("activate", lambda x:self.__emit_search())

        button = gtk.Button("Find Now")
        box2.pack_start(button, expand=0, fill=0)
        button.connect("clicked", lambda x:self.__emit_search())

        self.pack_start(box1, expand=0, fill=0)
        self.pack_start(box2, expand=0, fill=0)

        box1.show_all()
        box2.show_all()
        

gobject.type_register(SearchBar)
gobject.signal_new("search",
                   SearchBar,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_STRING,
                    gobject.TYPE_STRING,
                    gobject.TYPE_BOOLEAN,
                    gobject.TYPE_STRING))
