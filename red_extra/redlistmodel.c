/* -*- Mode: C; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */

/*
 * redlistmodel.c
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

#include "redlistmodel.h"

#define ITER_GET_INDEX(iter) (GPOINTER_TO_INT ((iter)->user_data))
#define ITER_SET_INDEX(iter, i) ((iter)->user_data = GINT_TO_POINTER(i))

#define red_list_model_length(model) ((model) && (model)->array ? (model)->array->len : 0)

static GObjectClass *parent_class = NULL;

static guint
red_list_model_get_flags (GtkTreeModel *tree_model)
{
    return 0;
}

static gint
red_list_model_get_n_columns (GtkTreeModel *tree_model)
{
    RedListModel *model = RED_LIST_MODEL (tree_model);
    return model->columns ? model->columns->len : 0;
}

static GType
red_list_model_get_column_type (GtkTreeModel *tree_model, gint index)
{
    RedListModel *model = RED_LIST_MODEL (tree_model);
    RedListModelColumn *col;

    g_assert (model->columns);
    g_assert (0 <= index && index < model->columns->len);

    col = g_ptr_array_index (model->columns, index);
    return col->type;
}

static gboolean
red_list_model_get_iter (GtkTreeModel *tree_model,
                         GtkTreeIter  *iter,
                         GtkTreePath  *path)
{
    RedListModel *model;
    gint *indices;
    gint depth;

    model = RED_LIST_MODEL (tree_model);
    if (red_list_model_length (model) == 0)
        return FALSE;

    depth = gtk_tree_path_get_depth (path);
    if (depth != 1)
        return FALSE;

    indices = gtk_tree_path_get_indices (path);

    ITER_SET_INDEX(iter, indices[0]);
    return TRUE;
}

static GtkTreePath *
red_list_model_get_path (GtkTreeModel *tree_model,
                         GtkTreeIter  *iter)
{
    RedListModel *model;
    GtkTreePath *path;

    model = RED_LIST_MODEL (tree_model);
    if (red_list_model_length (model) == 0)
        return NULL;

    path = gtk_tree_path_new ();
    gtk_tree_path_append_index (path, ITER_GET_INDEX (iter));
    return path;
}

static void
red_list_model_get_value (GtkTreeModel *tree_model,
                          GtkTreeIter  *iter,
                          gint          column,
                          GValue       *value)
{
    RedListModel *model = RED_LIST_MODEL (tree_model);
    int i = ITER_GET_INDEX (iter);
    PyObject *obj, *py_value, *args;
    RedListModelColumn *col;

    g_assert (model->columns);
    g_assert (0 <= column && column < model->columns->len);

    g_assert (model->array);
    g_assert (0 <= i && i < model->array->len);

    obj = g_ptr_array_index (model->array, i);
    col = g_ptr_array_index (model->columns, column);

    args = Py_BuildValue("(O)", obj);
    py_value = PyEval_CallObject(col->pycallback, args);
    if (py_value == NULL) {
        g_value_init (value, G_TYPE_STRING);
        g_value_set_string (value, "ERROR!");
        return;
    }

    g_value_init (value, col->type);
    pyg_value_from_pyobject (value, py_value);
    Py_DECREF (py_value);
}

static gboolean
red_list_model_iter_next (GtkTreeModel *tree_model,
                          GtkTreeIter  *iter)
{
    RedListModel *model = RED_LIST_MODEL (tree_model);
    gint i = ITER_GET_INDEX (iter);

    ++i;
    if (i >= red_list_model_length (model))
        return FALSE;

    ITER_SET_INDEX (iter, i);
    return TRUE;
}

static gboolean
red_list_model_iter_children (GtkTreeModel *tree_model,
                              GtkTreeIter  *iter,
                              GtkTreeIter  *parent)
{
    RedListModel *model = RED_LIST_MODEL (tree_model);

    if (parent == NULL && red_list_model_length (model) > 0) {
        ITER_SET_INDEX (iter, 0);
        return TRUE;
    }
    
    return FALSE;
}

static gboolean
red_list_model_iter_has_child (GtkTreeModel *tree_model,
                               GtkTreeIter  *iter)
{
    return FALSE;
}

static gint
red_list_model_iter_n_children (GtkTreeModel *tree_model,
                                GtkTreeIter  *iter)
{
    return 0;
}

static gboolean
red_list_model_iter_nth_child (GtkTreeModel *tree_model,
                               GtkTreeIter  *iter,
                               GtkTreeIter  *parent,
                               gint          n)
{
    RedListModel *model = RED_LIST_MODEL (tree_model);
    if (parent == NULL && 0 <= n && n < red_list_model_length (model)) {
        ITER_SET_INDEX (iter, n);
        return TRUE;
    }
    return FALSE;
}

static gboolean
red_list_model_iter_parent (GtkTreeModel *tree_model,
                            GtkTreeIter  *iter,
                            GtkTreeIter  *child)
{
    return FALSE;
}

/* ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** */

static void
red_list_model_clear_columns (RedListModel *model)
{
    int i;

    if (model->columns == NULL)
        return;

    for (i = 0; i < model->columns->len; ++i) {
        RedListModelColumn *col = g_ptr_array_index (model->columns, i);
        Py_DECREF (col->pycallback);
        g_free (col);
    }

    g_ptr_array_free (model->columns, TRUE);
    model->columns = NULL;
}

static void
red_list_model_clear_array (RedListModel *model)
{
    int i;

    if (model->array == NULL)
        return;

    for (i = 0; i < model->array->len; ++i) {
        PyObject *obj = g_ptr_array_index (model->array, i);
        Py_DECREF (obj);
    }

    g_ptr_array_free (model->array, TRUE);
    model->array = NULL;
}

/* ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** */

void
red_list_model_finalize (GObject *obj)
{
    RedListModel *model = RED_LIST_MODEL (obj);

    red_list_model_clear_columns (model);
    red_list_model_clear_array (model);

    if (parent_class->finalize)
        parent_class->finalize (obj);
}

static void
red_list_model_class_init (RedListModelClass *klass)
{
    GObjectClass *obj_class = (GObjectClass *) klass;

    parent_class = g_type_class_peek_parent (klass);

    obj_class->finalize = red_list_model_finalize;
}

static void
red_list_model_init (RedListModel *self)
{

}

static void
red_list_model_iface_init (GtkTreeModelIface *iface)
{
    iface->get_flags       = red_list_model_get_flags;
    iface->get_n_columns   = red_list_model_get_n_columns;
    iface->get_column_type = red_list_model_get_column_type;
    iface->get_iter        = red_list_model_get_iter;
    iface->get_value       = red_list_model_get_value;
    iface->iter_next       = red_list_model_iter_next;
    iface->iter_children   = red_list_model_iter_children;
    iface->iter_has_child  = red_list_model_iter_has_child;
    iface->iter_n_children = red_list_model_iter_n_children;
    iface->iter_nth_child  = red_list_model_iter_nth_child;
    iface->iter_parent     = red_list_model_iter_parent;
}

GType
red_list_model_get_type (void)
{
    static GType object_type = 0;

    if (! object_type) {
        
        static const GTypeInfo object_info = {
            sizeof (RedListModelClass),
            NULL, NULL,
            (GClassInitFunc) red_list_model_class_init,
            NULL, NULL,
            sizeof (RedListModel),
            0,
            (GInstanceInitFunc) red_list_model_init
        };

        static const GInterfaceInfo tree_model_info = {
            (GInterfaceInitFunc) red_list_model_iface_init,
            NULL, NULL
        };

        object_type = g_type_register_static (G_TYPE_OBJECT,
                                              "RedListModel",
                                              &object_info, 0);

        g_type_add_interface_static (object_type,
                                     GTK_TYPE_TREE_MODEL,
                                     &tree_model_info);

    }

    return object_type;
}

RedListModel *
red_list_model_new (void)
{
    return RED_LIST_MODEL (g_object_new (RED_TYPE_LIST_MODEL, NULL));
}

/* ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** */

void
red_list_model_set_list (RedListModel *model,
                         PyObject     *pylist)
{
    int i, N;

    g_return_if_fail (RED_IS_LIST_MODEL (model));
    g_return_if_fail (pylist != NULL);

    red_list_model_clear_array (model);

    N = PyList_Size (pylist);

    if (model->array == NULL)
        model->array = g_ptr_array_new ();

    for (i = 0; i < N; ++i) {
        PyObject *obj = PyList_GET_ITEM (pylist, i);
        Py_INCREF (obj);
        g_ptr_array_add (model->array, obj);
    }
}

gint
red_list_model_add_column (RedListModel *model,
                           PyObject     *pycallback,
                           GType         type)
{
    RedListModelColumn *col;

    g_return_if_fail (RED_IS_LIST_MODEL (model));
    g_return_if_fail (pycallback != NULL);
    g_return_if_fail (PyCallable_Check (pycallback));

    col = g_new0 (RedListModelColumn, 1);
    col->pycallback = pycallback;
    col->type = type;
    
    Py_INCREF (pycallback);

    if (model->columns == NULL)
        model->columns = g_ptr_array_new ();

    g_ptr_array_add (model->columns, col);

    return model->columns->len - 1;
}
