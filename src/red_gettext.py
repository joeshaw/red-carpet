###
### Copyright (C) 2003 Ximian, Inc.
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

import os

import gettext

# FIXME: We'll probably have to add in the localedir for things like
# Solaris which put locale files in /usr/lib/locale instead of
# /usr/share/locale; python looks in the latter.
t = None
try:
    t = gettext.translation("red-carpet", "/opt/rc2/share/locale")
except IOError: # No translation file for this language
    pass

debug = os.getenv("RC_GUI_TRANSLATION_DEBUG")

def _(msg):
    if debug:
        return "((%s))" % msg
    else:
        if t:
            return t.ugettext(msg)
        else:
            return msg



