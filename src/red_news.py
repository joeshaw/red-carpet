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

import string, re
import rcd_util
import gobject, gtk, pango
import red_component

model = None

class NewsView(gtk.ScrolledWindow):

    def __init__(self):
        gtk.ScrolledWindow.__init__(self)

        global model
        if not model:
            server = rcd_util.get_server()
            model = NewsModel(server)

        view = gtk.TreeView(model)

        view.set_headers_visible(0)
        view.set_rules_hint(1)
        sel = view.get_selection()
        sel.set_mode(gtk.SELECTION_NONE)

        col = gtk.TreeViewColumn("Icon",
                                 gtk.CellRendererPixbuf(),
                                 pixbuf=COLUMN_ICON)

        view.append_column(col)

        col = gtk.TreeViewColumn()
        r1 = gtk.CellRendererText()
        col.pack_start(r1, 0)
        col.set_attributes(r1, markup=COLUMN_TITLE)

        view.append_column(col)

        view.show_all()

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.add(view)


class NewsComponent(red_component.Component):

    def name(self):
        return "News"

    def long_name(self):
        return "Red Carpet News"

    def show_in_shortcuts(self):
        return 1

    def accelerator(self):
        return "<Control>n"

    def pixbuf(self):
        return "news"

    def build(self):
        page = gtk.VBox(0, 6)

        hbox = gtk.HBox(0, 6)

        label = gtk.Label("")
        label.set_alignment(0, 0.5)
        label.set_markup("<b>" + self.long_name() + "</b>")
        hbox.pack_start(label)

        hbox.show_all()
        page.pack_start(hbox, 0, 0)

        view = NewsView()
        view.show()
        page.pack_start(view, 1, 1)

        return page


COLUMN_NEWS        = 0
COLUMN_ICON        = 1
COLUMN_TITLE       = 2
COLUMN_DATE        = 3
COLUMN_LAST        = 4


class NewsModel(gtk.GenericTreeModel):

    def __init__(self, server):
        gtk.GenericTreeModel.__init__(self)
        self.news = server.rcd.news.get_all()

        for item in self.news:
            item["icon"] = self.get_icon(item["channel_name"])

    def get_icon(self, name):
        # FIXME: Special hacks for current (bad) news file
        if name == "Ximian GNOME":
            name = "Ximian Desktop"

        if name == "OpenOffice":
            name = "OpenOffice.org"

        channels = rcd_util.get_all_channels()
        for c in channels:
            if c["name"] == name:
                return rcd_util.get_channel_icon(c["id"])

        return None

    def news_item_to_column(self, news_item, index):
        if index == COLUMN_NEWS:
            return news_item
        elif index == COLUMN_ICON:
            return news_item["icon"]
        elif index == COLUMN_TITLE:
            summary = re.sub("\s+", " ", news_item["summary"])

            # Break the news item up to make it easier to read.
            # FIXME: It would be nice to actually wrap the text in
            # some sort of intelligent way.
            lines = rcd_util.linebreak(summary, 72)
            summary = string.join(lines, "\n")
            
            return "<b>" + news_item["title"] + "</b>\n<i>" + news_item["time_str"] + "</i>\n" + summary
        elif index == COLUMN_DATE:
            return "\n" + news_item["time_str"]

    def on_get_flags(self):
        return 0

    def on_get_n_columns(self):
        return COLUMN_LAST

    def on_get_column_type(self, index):
        if index == COLUMN_NEWS:
            return gobject.TYPE_PYOBJECT
        elif index == COLUMN_ICON:
            return gtk.gdk.Pixbuf
        else:
            return gobject.TYPE_STRING

    def on_get_path(self, node):
        return node

    def on_get_iter(self, path):
        return path

    def on_get_value(self, node, column):
        news_item = self.news[node[0]]
        if news_item:
            return self.news_item_to_column(news_item, column)
        return "???"

    def on_iter_next(self, node):
        next = node[0] + 1
        if next >= len(self.news):
            return None
        return (next,)

    def on_iter_children(self, node):
        if node == None:
            return (0,)
        else:
            return None

    def on_iter_has_child(self, node):
        return 0;

    def on_iter_nth_child(self, node, n):
        if node == None and n == 0:
            return (0,)
        else:
            return None

    def on_iter_parent(self, node):
        return None
