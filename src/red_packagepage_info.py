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

import re
import gtk
import rcd_util, red_packagepage
import red_pixbuf
from red_gettext import _

NO_SPAN = 0
SPAN    = 1

TYPE_TEXT   = 0
TYPE_WIDGET = 1

re_whitespace = re.compile("\s+")

def pkg_element(pkg, pkg_info, key):
    return str(pkg.get(key, ""))

def pkg_info_element(pkg, pkg_info, key):
    return str(pkg_info.get(key, ""))

def pkg_size(pkg, pkg_info, key):
    size = pkg_info.get(key, "")
    if not size:
        size = 0
    return rcd_util.byte_size_to_string(size)

def pkg_channel(pkg, pkg_info, key):
    name = rcd_util.get_package_channel_name(pkg)
    if not name or name == "????": # evil magic failure code
        return None
    icon = rcd_util.get_package_channel_icon(pkg, width=24, height=24)
    box = gtk.HBox(0, 2)
    if icon:
        img = gtk.Image()
        img.set_from_pixbuf(icon)
        box.pack_start(img, 0, 0)
    label = gtk.Label(name)
    box.pack_start(label, 0, 0)
    return box

def pkg_section(pkg, pkg_info, key):
    box = gtk.HBox(0, 2)
    icon = pkg.get("section_str", "")
    if icon:
        icon = "section-%s" % icon
        box.pack_start(red_pixbuf.get_widget(icon, width=24, height=24), 0, 0)
    label = pkg.get("section_user_str")
    if label:
        box.pack_start(gtk.Label(label), 0, 0)
    return box

def pkg_description(pkg, pkg_info, key):
    txt = pkg_info_element(pkg, pkg_info, key)
    txt = re.sub(re_whitespace, " ", txt.strip())
    l = gtk.Label(txt)
    l.set_alignment(0, 0.5)
    l.set_property("wrap", 1)
    return l

_info_rows = (
    (_("Name"),           TYPE_TEXT,   pkg_element,      "name",           NO_SPAN),
    (_("Version"),        TYPE_TEXT,   pkg_element,      "version",        NO_SPAN),
    (_("Release"),        TYPE_TEXT,   pkg_element,      "release",        NO_SPAN),
    (_("Package Size"),   TYPE_TEXT,   pkg_size,         "file_size",      NO_SPAN),
    (_("Installed Size"), TYPE_TEXT,   pkg_size,         "installed_size", NO_SPAN),
    (_("Channel"),        TYPE_WIDGET, pkg_channel,      "channel",        NO_SPAN),
    (_("Section"),        TYPE_WIDGET, pkg_section,      "section",        NO_SPAN),
    (_("Summary"),        TYPE_TEXT,   pkg_info_element, "summary",        NO_SPAN),
    (_("Description"),    TYPE_WIDGET, pkg_description,  "description",    SPAN),
    )

def build_rows(table, pkg, pkg_info):
    rindex = 0
    for r in range(0, len(_info_rows)):
        v = _info_rows[r][2](pkg, pkg_info, _info_rows[r][3])

        if not v:
            continue

        label = gtk.Label("")
        label.set_markup("<b>" + _info_rows[r][0] + ":</b>")
        label.set_alignment(0, 0.5)

        if _info_rows[r][1] == TYPE_TEXT:
            value = gtk.Label(v)
            value.set_alignment(0, 0.5)
        else:
            value = v

        if value is not None:
            if _info_rows[r][4] == NO_SPAN:
                table.attach(label,
                             0, 1, rindex, rindex + 1,
                             gtk.FILL, gtk.FILL,
                             5, 3)

                table.attach(value,
                             1, 2, rindex, rindex + 1,
                             gtk.EXPAND | gtk.FILL, gtk.FILL,
                             5, 3)

                rindex = rindex + 1
            else:
                table.attach(label,
                             0, 2, rindex, rindex + 1,
                             gtk.FILL, gtk.FILL,
                             5, 3)

                table.attach(value,
                             0, 2, rindex + 1, rindex + 2,
                             gtk.FILL, gtk.FILL,
                             5, 3)

            rindex = rindex + 2


class PackagePage_Info(red_packagepage.PackagePage):

    def __init__(self):
        red_packagepage.PackagePage.__init__(self)

    def name(self):
        return _("Info")

    def visible(self, pkg):
        return 1

    def build_widget(self, pkg, server):
        table = gtk.Table(7, 2, 0)
        build_rows(table, pkg, rcd_util.get_package_info(pkg))
        return table

