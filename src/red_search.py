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
import gtk
import rcd_util
import red_header, red_pixbuf, red_menubar
import red_packagearray, red_channeloption, red_packagetable
import red_component

class SearchComponent(red_component.Component):

    def __init__(self):
        red_component.Component.__init__(self)
        self.match_anyall = "all"
        self.match_substr = "substr"
        self.match_status = "all"
        self.search_desc = 1

    def name(self):
        return "Search"

    def pixbuf(self):
        return "info-button"

    def get_match_anyall(self):
        return self.match_anyall

    def set_match_anyall(self, x):
        assert x in ["any", "all"]
        self.match_anyall = x
        self.do_query()

    def get_match_word(self):
        return self.match_substr

    def set_match_word(self, x):
        assert x in ["whole", "substr"]
        self.match_substr = x
        self.do_query()

    def get_match_status(self):
        return self.match_status

    def set_match_status(self, x):
        assert x in ["all", "installed", "uninstalled"]
        self.match_status = x
        self.do_query()

    def get_search_descriptions(self):
        return self.search_desc

    def set_search_descriptions(self, x):
        self.search_desc = x
        self.do_query()

    def do_query(self):
        text = self.search_data.get_text()

        if self.search_desc:
            key = "text"
        else:
            key = "name"

        if self.match_substr == "substr":
            match = "contains"
        else:
            match = "contains_word"

        query = []

        for t in string.split(text):
            query.append([key, match, t])

        if query and self.match_anyall == "any":
            query.insert(0, ["", "begin-or", ""])
            query.append(["", "end-or", ""])

        if self.match_status == "installed":
            query.append(["installed", "=", "true"])
        elif self.match_status == "uninstalled":
            query.append(["installed", "=", "false"])
            
        self.array.set_query(query)

    def build(self):
        self.array = red_packagearray.PackagesFromQuery(self.server())

        ### Upper

        hbox = gtk.HBox(0,0)

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

        bar.add("/Search/Sep3", is_separator=1)

        bar.add("/Search/Search All Packages",
                radiogroup="which", radiotag="all",
                radio_get=lambda: self.get_match_status(),
                radio_set=lambda x: self.set_match_status(x))
        bar.add("/Search/Search Only Installed Packages",
                radiogroup="which", radiotag="installed")
        bar.add("/Search/Search Only Uninstalled Packages",
                radiogroup="which", radiotag="uninstalled")
        hbox.pack_start(bar, 0, 0, 0)

        self.search_data = gtk.Entry()
        hbox.pack_start(self.search_data, 1, 1, 0)

        button = gtk.Button("Find Now")
        hbox.pack_start(button, 0, 0, 0)

        #self.array.set_query([])
        self.search_data.connect("activate", lambda x:self.do_query())
        button.connect("clicked", lambda x:self.do_query())
        
        hbox.show_all()
        self.display("upper", hbox)


        ### Main

        ex = red_packagetable.PackageTable()
        ex.set_exploder(by_channel=1)
        ex.set_array(self.array)
            
        self.display("main", ex)

    def changed_visibility(self, flag):
        if flag:
            self.array.thaw()
        else:
            self.array.freeze()
        
