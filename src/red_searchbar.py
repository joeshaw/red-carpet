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

import string
import gobject, gtk
import red_menubar
import red_channeloption, red_sectionoption, red_statusoption

from red_gettext import _

class SearchBar(gtk.VBox):

    def __init__(self):
        gobject.GObject.__init__(self)
        self.set_spacing(6)
        self.match_anyall = "all"
        self.match_substr = "substr"
        self.search_desc = 1
        self.__assemble()
        
    def __emit_search(self):
        self.emit("search",
                  self.get_query(),
                  self.get_filter())

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

    def get_query(self):
        query = []

        if self.search_desc:
            search_key = "text"
        else:
            search_key = "name"

        if self.match_substr == "substr":
            search_match = "contains"
        else:
            search_match = "contains_word"

        text = self.get_search_text()
        if text:
            for t in string.split(text):
                query.append([search_key, search_match, t])

        if query and self.match_anyall == "any":
            query.insert(0, ["", "begin-or", ""])
            query.append(["", "end-or", ""])

        id = self.__channel_opt.get_channel_id()
        if id >= 0:
            query.append(["channel", "is", str(id)])

        return query

    def get_filter(self):
        return self.__status_opt and self.__status_opt.get_current_filter()

    def get_search_entry(self):
        return self.search_entry

    def __assemble(self):

        box1 = gtk.HBox(0, 0)
        box2 = gtk.HBox(0, 0)

        ###
        ### Build the top row of the bar, where we can filter by
        ### channel, status, etc.

        # When the string is marked for translation, the magic codes allow
        # the menu items to be reordered.
        txt = _("Search for %status packages in %channel ")

        txt_parsed = []
        while txt:
            i = txt.find("%")
            if i < 0:
                fragment = txt
                txt = ""
            elif i == 0:
                j = txt.find(" ")
                if j >= 0:
                    fragment = txt[:j]
                    txt = txt[j:]
                else:
                    fragment = txt
                    txt = ""
            else:
                fragment = txt[:i]
                txt = txt[i:]

            fragment = fragment.strip()
            if fragment:
                txt_parsed.append(fragment)

        ch_opt   = red_channeloption.ChannelOption(allow_any_channel=1,
                                                   allow_no_channel=0)
        stat_opt = red_statusoption.StatusOption()

        ch_opt.connect_after("selected",
                             lambda chopt, id, bar: bar.__emit_search(),
                             self)
        stat_opt.connect_after("selected",
                               lambda statopt, fn, bar: bar.__emit_search(),
                               self)

        for fragment in txt_parsed:
            if fragment == "%channel":
                box1.pack_start(ch_opt, expand=0, fill=0, padding=3)
            elif fragment == "%status":
                box1.pack_start(stat_opt, expand=0, fill=0, padding=3)
            else:
                box1.pack_start(gtk.Label(fragment), expand=0, fill=0)

        ###
        ### Put together second row, with the search entry and dropdown
        ### button w/ search characteristics.
        ###

        dropdown = "/" + _("Containing")

        bar = red_menubar.MenuBar()
        bar.add(dropdown, with_dropdown_arrow=1)

        bar.add(dropdown+"/"+_("Match All Words"),
                radiogroup="anyall", radiotag="all",
                radio_get=lambda: self.get_match_anyall(),
                radio_set=lambda x: self.set_match_anyall(x))
        bar.add(dropdown+"/"+_("Match Any Word"),
                radiogroup="anyall", radiotag="any")

        bar.add(dropdown+"/Sep1", is_separator=1)

        bar.add(dropdown+"/"+_("Match Substrings"),
                radiogroup="words", radiotag="substr",
                radio_get=lambda: self.get_match_word(),
                radio_set=lambda x: self.set_match_word(x))
        bar.add(dropdown+"/"+_("Match Whole Words"),
                radiogroup="words", radiotag="whole")

        bar.add(dropdown+"/Sep2", is_separator=1)

        bar.add(dropdown+"/"+_("Search Descriptions"),
                checked_get = lambda: self.get_search_descriptions(),
                checked_set = lambda x: self.set_search_descriptions(x))

        box2.pack_start(bar, expand=0, fill=0)

        self.search_entry = gtk.Entry()
        box2.pack_start(self.search_entry, expand=1, fill=1)
        self.search_entry.connect("activate", lambda x:self.__emit_search())

        self.pack_start(box1, expand=0, fill=0)
        self.pack_start(box2, expand=0, fill=0)

        box1.show_all()
        box2.show_all()

        self.__status_opt = stat_opt
        self.__channel_opt = ch_opt
        

gobject.type_register(SearchBar)
gobject.signal_new("search",
                   SearchBar,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,  # query
                    gobject.TYPE_PYOBJECT)) # filter

