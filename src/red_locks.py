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

import rcd_util
import red_serverlistener
from red_gettext import _

def toggle_lock(pkg):
    if not pkg:
        return

    server = rcd_util.get_server_proxy()

    def ready_cb(th):
        try:
            success = th.get_result()
        except ximian_xmlrpclib.Fault, f:
            rcd_util.dialog_from_fault(f)
            return
        red_serverlistener.reset_polling(1)

    locked = pkg.get("locked")
    if not locked:
        th = server.rcd.packsys.add_lock({"glob":pkg["name"]})
    else:
        th = server.rcd.packsys.remove_lock({"glob":pkg["name"]})

    th.connect("ready", ready_cb)
