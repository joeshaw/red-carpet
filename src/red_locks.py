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

import rcd_util

def toggle_lock(pkg):
    if not pkg:
        return

    server = rcd_util.get_server()

    locked = pkg.get("locked")
    if not locked:
        server.rcd.packsys.add_lock({"glob":pkg["name"]})
    else:
        try:
            server.rcd.packsys.remove_lock({"glob":pkg["name"]})
        except:
            pass
