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

import string, re
import rcd_util
import gobject, gtk, pango
import red_component
import red_listmodel
import red_thrashingtreeview
import red_serverlistener
from red_gettext import _


def news_item_get_title(item):
    summary = re.sub("\s+", " ", item["summary"])

    # Break the news item up to make it easier to read.
    # FIXME: It would be nice to actually wrap the text in
    # some sort of intelligent way.
    lines = rcd_util.linebreak(summary, 72)
    summary = string.join(lines, "\n")

    return "<b>" + item["title"] + "</b>\n<i>" + item["time_str"] + "</i>\n" + summary

def news_item_get_date(item):
    return "\n" + item["time_str"]

COLUMNS = (
    ("ITEM",
     lambda x:x,
     gobject.TYPE_PYOBJECT),

    ("ICON",
     lambda x:x["icon"],
     gtk.gdk.Pixbuf),

    ("TITLE",
     lambda x:news_item_get_title(x),
     gobject.TYPE_STRING),

    ("DATE",
     lambda x:news_item_get_date(x),
     gobject.TYPE_STRING),
    )

for i in range(len(COLUMNS)):
    name = COLUMNS[i][0]
    exec("COLUMN_%s = %d" % (name, i))


class NewsModel(red_listmodel.ListModel, red_serverlistener.ServerListener):

    def __init__(self):
        red_listmodel.ListModel.__init__(self)
        red_serverlistener.ServerListener.__init__(self)

        self.__worker = None
        self.__worker_handler_id = 0

        for name, callback, type in COLUMNS:
            self.add_column(callback, type)

        self.refresh()

    def set_news(self, news):
        def set_news_cb(this, n):
            this.__news = n
        self.changed(set_news_cb, news)

    def refresh(self):

        if self.__worker:
            if self.__worker_handler_id:
                self.__worker.disconnect(self.__worker_handler_id)
                self.__worker_handler_is = 0
            self.__worker.cancel()

        def get_news_cb(worker, this):
            if not worker.is_cancelled():
                try:
                    news = worker.get_result()
                except ximian_xmlrpclib.Fault, f:
                    rcd_util.dialog_from_fault(f)
                    return
                if news:
                    for item in news:
                        item["icon"] = this.get_icon(item["channel_name"])

                    this.set_news(news)

        self.set_news([])

        server = rcd_util.get_server_proxy()
        self.__worker = server.rcd.news.get_all()
        self.__worker_handler_id = self.__worker.connect("ready",
                                                         get_news_cb,
                                                         self)

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


    def get_all(self):
        return self.__news

    def channels_changed(self):
        self.refresh()


class NewsView(gtk.ScrolledWindow):

    def __init__(self):
        gtk.ScrolledWindow.__init__(self)

        model = NewsModel()

        view = red_thrashingtreeview.TreeView()
        view.set_model(model)

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
        self.set_shadow_type(gtk.SHADOW_OUT)
        self.add(view)


class NewsComponent(red_component.Component):

    def name(self):
        return _("News")

    def long_name(self):
        return _("Red Carpet News")

    def access_key(self):
        return "n"

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
