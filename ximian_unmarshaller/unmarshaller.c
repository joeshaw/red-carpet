/* -*- Mode: C; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */

/*
 * unmarshaller.c
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

#include <glib.h>
#include <Python.h>

staticforward PyTypeObject PyUnmarshallerType;

enum PyUnmarshallerType {
    PY_UNMARSHALLER_TYPE_NONE,
    PY_UNMARSHALLER_TYPE_PARAMS,
    PY_UNMARSHALLER_TYPE_FAULT,
    PY_UNMARSHALLER_TYPE_METHODNAME
};

typedef struct {
    PyObject_HEAD;
    enum PyUnmarshallerType type;
    GPtrArray *stack;
    GSList    *marks;
    GString   *data;
    char      *methodname;
    char      *encoding;
    int        value;
    PyObject  *binary_cb;
} PyUnmarshaller;
    
static PyObject *
unmarshaller_close (PyObject *self, PyObject *args)
{
    PyUnmarshaller *unm = (PyUnmarshaller *) self;
    PyObject *tuple;
    int i;

    /* tuple-ify the stack */
    tuple = PyTuple_New (unm->stack->len);
    for (i = 0; i < unm->stack->len; ++i) {
        PyObject *obj = g_ptr_array_index (unm->stack, i);
        PyTuple_SetItem (tuple, i, obj);
        Py_INCREF (obj);
        ++i;
    }

    return tuple;
}

static PyObject *
unmarshaller_getmethodname (PyObject *self, PyObject *args)
{
    PyUnmarshaller *unm = (PyUnmarshaller *) self;

    if (unm->methodname) 
        return Py_BuildValue ("s", unm->methodname);

    Py_INCREF (Py_None);
    return Py_None;
}

static PyObject *
unmarshaller_xml (PyObject *self, PyObject *args)
{
    PyUnmarshaller *unm = (PyUnmarshaller *) self;
    char *encoding;
    int standalone;

    /* FIXME: do nothing for now */

#if 0
    if (! PyArg_ParseTuple (args, "si", &encoding, &standalone))
        return NULL;

    g_free (unm->encoding);
    unm->encoding = g_strdup (encoding);

    g_assert (standalone);
#endif

    Py_INCREF (Py_None);
    return Py_None;
}

static PyObject *
unmarshaller_start (PyObject *self, PyObject *args)
{
    PyUnmarshaller *unm = (PyUnmarshaller *) self;
    PyObject *dummy;
    char *tag;

    if (! PyArg_ParseTuple (args, "sO", &tag, &dummy))
        return NULL;

    if (!strcmp (tag, "array") || !strcmp (tag, "struct"))
        unm->marks =
            g_slist_prepend (unm->marks,
                             GINT_TO_POINTER (unm->stack->len));

    g_string_assign (unm->data, "");

    unm->value = !strcmp (tag, "value");

    Py_INCREF (Py_None);
    return Py_None;
}

static PyObject *
unmarshaller_data (PyObject *self, PyObject *args)
{
    PyUnmarshaller *unm = (PyUnmarshaller *) self;
    char *data_str;

    if (! PyArg_ParseTuple (args, "s", &data_str))
        return NULL;
    
    g_string_append (unm->data, data_str);

    Py_INCREF (Py_None);
    return Py_None;
}

/* ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** */

static void
end_boolean (PyUnmarshaller *unm, const char *data)
{
    PyObject *obj = NULL;

    if (! strcmp (data, "0"))
        obj = Py_BuildValue ("i", 0);
    else if (! strcmp (data, "1"))
        obj = Py_BuildValue ("i", 1);

    if (obj == NULL) {
        g_assert_not_reached ();
    }

    g_ptr_array_add (unm->stack, obj);
    unm->value = 0;
}

static void
end_int (PyUnmarshaller *unm, const char *data)
{
    PyObject *obj = Py_BuildValue ("i", atoi (data));
    g_ptr_array_add (unm->stack, obj);
    unm->value = 0;
}

static void
end_double (PyUnmarshaller *unm, const char *data)
{
    PyObject *obj = Py_BuildValue ("d", atof (data));
    g_ptr_array_add (unm->stack, obj);
    unm->value = 0;
}

static void
end_string (PyUnmarshaller *unm, const char *data)
{
    /* FIXME: ignores all issues regarding the encoding of the data */
    PyObject *obj = Py_BuildValue ("s", data);
    g_ptr_array_add (unm->stack, obj);
    unm->value = 0;
}

static void
end_array (PyUnmarshaller *unm, const char *data)
{
    PyObject *list;
    int mark, i;
    
    g_assert (unm->marks);
    mark = GPOINTER_TO_INT (unm->marks->data);
    
    unm->marks = g_slist_delete_link (unm->marks,
                                      unm->marks);

    list = PyList_New (unm->stack->len - mark);

    for (i = mark; i < unm->stack->len; ++i) {
        PyObject *obj = g_ptr_array_index (unm->stack, i);
        PyList_SetItem (list, i - mark, obj);
    }

    g_ptr_array_set_size (unm->stack, mark);
    g_ptr_array_add (unm->stack, list);
    
    unm->value = 0;
}

static void
end_struct (PyUnmarshaller *unm, const char *data)
{
    PyObject *dict;
    int mark, i;

    g_assert (unm->marks);
    mark = GPOINTER_TO_INT (unm->marks->data);
    
    unm->marks = g_slist_delete_link (unm->marks,
                                      unm->marks);

    dict = PyDict_New ();

    for (i = mark; i < unm->stack->len; i += 2) {
        PyObject *key = g_ptr_array_index (unm->stack, i);
        PyObject *value = g_ptr_array_index (unm->stack, i+1);

        PyDict_SetItem (dict, key, value);
    }

    g_ptr_array_set_size (unm->stack, mark);
    g_ptr_array_add (unm->stack, dict);
    
    unm->value = 0;
}

static void
end_base64 (PyUnmarshaller *unm, const char *data)
{
    PyObject *binary;
    PyObject *args;

    args = Py_BuildValue ("(s)", data);
    binary = PyEval_CallObject (unm->binary_cb, args);

    g_ptr_array_add (unm->stack, binary);

    unm->value = 0;
}

static void
end_dateTime (PyUnmarshaller *unm, const char *data)
{
    g_assert_not_reached ();
}

static void
end_value (PyUnmarshaller *unm, const char *data)
{
    if (unm->value)
        end_string (unm, data);
}

static void
end_params (PyUnmarshaller *unm, const char *data)
{
    unm->type = PY_UNMARSHALLER_TYPE_PARAMS;
}

static void
end_fault (PyUnmarshaller *unm, const char *data)
{
    unm->type = PY_UNMARSHALLER_TYPE_FAULT;
}

static void
end_methodName (PyUnmarshaller *unm, const char *data)
{
    g_free (unm->methodname);
    unm->methodname = g_strdup (data);
    unm->type = PY_UNMARSHALLER_TYPE_METHODNAME;
}

static PyObject *
unmarshaller_end (PyObject *self, PyObject *args)
{
    PyUnmarshaller *unm = (PyUnmarshaller *) self;
    char *tag;
    char *data_str = NULL;

    if (! PyArg_ParseTuple (args, "s", &tag))
        return NULL;

    data_str = unm->data->str;

    /* FIXME: need to finish implementing tags */

    if (! strcmp (tag, "boolean")) {
        end_boolean (unm, data_str);
    } else if (! strcmp (tag, "i4") || ! strcmp (tag, "int")) {
        end_int (unm, data_str);
    } else if (! strcmp (tag, "double")) {
        end_double (unm, data_str);
    } else if (! strcmp (tag, "string") || ! strcmp (tag, "name")) {
        end_string (unm, data_str);
    } else if (! strcmp (tag, "array")) {
        end_array (unm, data_str);
    } else if (! strcmp (tag, "struct")) {
        end_struct (unm, data_str);
    } else if (! strcmp (tag, "base64")) {
        end_base64 (unm, data_str);
    } else if (! strcmp (tag, "value")) {
        end_value (unm, data_str);
    } else if (! strcmp (tag, "params")) {
        end_params (unm, data_str);
    } else if (! strcmp (tag, "fault")) {
        end_fault (unm, data_str);
    } else {
        /* g_print ("*** Unknown tag '%s'\n", tag); */
    }

    Py_INCREF (Py_None);
    return Py_None;
}

/* ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** */

static PyObject *
unmarshaller_new (PyObject *self, PyObject *args)
{
    PyUnmarshaller *unm;
    PyObject *binary_cb;

    if (!PyArg_ParseTuple (args, "O:new_unmarshaller", &binary_cb))
        return NULL;
    
    unm = PyObject_New (PyUnmarshaller, &PyUnmarshallerType);

    unm->type = PY_UNMARSHALLER_TYPE_NONE;
    unm->stack = g_ptr_array_new ();
    unm->marks = NULL;
    unm->data = g_string_new ("");
    unm->methodname = NULL;
    unm->encoding = g_strdup ("utf-8");
    unm->binary_cb = binary_cb;

    Py_INCREF (unm->binary_cb);

    return (PyObject *) unm;
}

static void
unmarshaller_dealloc (PyObject *self)
{
    PyUnmarshaller *unm = (PyUnmarshaller *) self;

    /* FIXME: leaking objects on stack */
    g_ptr_array_free (unm->stack, TRUE);
    g_slist_free (unm->marks);
    g_string_free (unm->data, TRUE);
    g_free (unm->methodname);
    g_free (unm->encoding);

    PyObject_Del (self);
}

static PyMethodDef unmarshaller_methods[] = {
    { "close", unmarshaller_close, METH_VARARGS, "close" },
    { "getmethodname", unmarshaller_getmethodname, METH_VARARGS, "getmethodname" },
    { "xml",   unmarshaller_xml,   METH_VARARGS, "xml" },

    { "start", unmarshaller_start, METH_VARARGS, "start" },
    { "data",  unmarshaller_data,  METH_VARARGS, "data" },
    { "end",   unmarshaller_end,   METH_VARARGS, "end" },
    { NULL, NULL, 0, NULL }
};

static PyObject *
unmarshaller_getattr (PyUnmarshaller *unm, char *name)
{
    return Py_FindMethod (unmarshaller_methods, (PyObject *) unm, name);
}

static PyTypeObject PyUnmarshallerType = {
    PyObject_HEAD_INIT (NULL)
    0,
    "ximian_unmarshaller",
    sizeof (PyUnmarshaller),
    0,
    unmarshaller_dealloc,
    0, /* tp_print */  
    (getattrfunc) unmarshaller_getattr,
    0, /*tp_setattr*/
    0, /*tp_compare*/
    0, /*tp_repr*/
    0, /*tp_as_number*/
    0, /*tp_as_sequence*/
    0, /*tp_as_mapping*/
    0, /*tp_hash */
};

static PyMethodDef general_methods[] = {
    { "new", unmarshaller_new, METH_VARARGS, "Create a new unmarshaller" },
    { NULL, NULL, 0, NULL }
};

DL_EXPORT (void)
initximian_unmarshaller (void)
{
    PyUnmarshallerType.ob_type = &PyType_Type;

    Py_InitModule("ximian_unmarshaller",
                  general_methods);
}
