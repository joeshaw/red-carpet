/* -*- Mode: C; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */

/*
 * module.c
 *
 * Copyright (C) 2002 Ximian, Inc.
 *
 */

/*
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
 * USA.
 */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <pygobject.h>

void red_register_classes (PyObject *d);

extern PyMethodDef red_functions[];

DL_EXPORT(void)
initxxx_red_extra(void)
{
    PyObject *m, *d;

    init_pygobject ();

    m = Py_InitModule("xxx_red_extra", red_functions);
    d = PyModule_GetDict (m);

    red_register_classes (d);

    if (PyErr_Occurred ()) {
        Py_FatalError ("Can't initialize module red_extra");
    }
}

