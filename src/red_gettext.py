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

t = None

def init(localedir):
    global t
    
    try:
        t = gettext.translation("red-carpet", localedir)
    except IOError: # No translation file for this language
        pass

debug = os.getenv("RC_GUI_TRANSLATION_DEBUG")

def _(msg):
    if debug:
        return "((%s))" % msg
    else:
        global t
        
        if t:
            return t.gettext(msg)
        else:
            return msg



