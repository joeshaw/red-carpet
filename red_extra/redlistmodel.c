/* -*- Mode: C; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */

/*
 * redlistmodel.c
 *
 * Copyright (C) 2002-2003 Ximian, Inc.
 *
 *
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

#define red_list_model_array_length(model) ((model) && (model)->array ? (model)->array->len : 0)

static GObjectClass *parent_class = NULL;

/* ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** */

/* Indexing */

static int
index_sort_fn (gconstpointer a_ptr,
               gconstpointer b_ptr,
               gpointer      user_data)
{
    RedListModel *model = user_data;
    gint a, b, cmp;
    PyObject *args, *val;

    a = *(const gint *) a_ptr;
    b = *(const gint *) b_ptr;
    
    args = Py_BuildValue ("(OO)",
                          g_ptr_array_index (model->array, a),
                          g_ptr_array_index (model->array, b));
    val  = PyEval_CallObject (model->sort_callback, args);

    g_assert (PyInt_Check (val));

    cmp = (gint) PyInt_AsLong (val);

    Py_DECREF (args);
    Py_DECREF (val);

    return cmp;
}

static void
red_list_model_build_index (RedListModel *model)
{
    gint len;

    if (model->index) {
        g_free (model->index);
        model->index = NULL;
        model->index_N = -1;
    }

    if (model->filter_callback == NULL && model->sort_callback == NULL)
        return;
    
    len = red_list_model_array_length (model);

    if (!len)
        return;

    /* We allocate the full length of the array, which is probably more
       space than we will actually need.  Oh well. */
    model->index = g_new (gint, len);
    model->index_N = 0;

    /* Use the filter callback to assemble a first version of the
       index. */
    if (model->filter_callback) {
        gint i;

        pyg_block_threads ();
        for (i = 0; i < len; ++i) {
            PyObject *obj = g_ptr_array_index (model->array, i);
            PyObject *args = Py_BuildValue ("(O)", obj);
            PyObject *val = PyEval_CallObject (model->filter_callback, args);
            if (val == NULL) {
                PyErr_Print ();
            } else {
                if (PyObject_IsTrue (val)) {
                    model->index[model->index_N] = i;
                    ++model->index_N;
                }
                Py_DECREF (args);
                Py_DECREF (val);
            }
        }
        pyg_unblock_threads ();
    }

    if (model->sort_callback) {

        /* If we don't have a filter, build up a trivial index so we have
           something to sort against. */
        if (!model->filter_callback) {
            gint i;
            for (i = 0; i < len; ++i)
                model->index[i] = i;
            model->index_N = len;
        }

        pyg_block_threads ();

        g_qsort_with_data (model->index,
                           model->index_N,
                           sizeof (gint),
                           index_sort_fn,
                           model);

        pyg_unblock_threads ();

        if (model->reverse_sort) {
            gint i, tmp;
            for (i = 0; i < model->index_N / 2; ++i) {
                tmp = model->index[i];
                model->index[i] = model->index[model->index_N-1-i];
                model->index[model->index_N-1-i] = tmp;
            }
        }
    }
}

/* ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** */

/* Implementation of the GtkTreeModel interface. */

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

    obj = red_list_model_get_list_item (model, i);
    g_assert (obj != NULL);

    col = g_ptr_array_index (model->columns, column);

    pyg_block_threads ();

    args = Py_BuildValue("(O)", obj);
    pyg_block_threads ();
    py_value = PyEval_CallObject(col->pycallback, args);
    pyg_unblock_threads ();
    Py_DECREF (args);
    if (py_value == NULL) {

        pyg_unblock_threads ();

        g_print ("error: col=%d i=%d len=%d\n",
                 column, i, model->array->len);
        g_value_init (value, G_TYPE_STRING);
        g_value_set_string (value, "ERROR!");

        return;
    }

    g_value_init (value, col->type);
    pyg_value_from_pyobject (value, py_value);
    Py_DECREF (py_value);

    pyg_unblock_threads ();
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

/* Implementation of the GtkTreeSortable interface. */

static gboolean
red_list_model_sortable_get_sort_column_id (GtkTreeSortable *sortable,
                                            gint            *sort_column_id,
                                            GtkSortType     *order)
{
    /* FIXME */
    return FALSE;
}

static void
red_list_model_sortable_set_sort_column_id (GtkTreeSortable *sortable,
                                            gint             sort_column_id,
                                            GtkSortType      order)
{
    /* FIXME */
}

static void
red_list_model_sortable_set_sort_func (GtkTreeSortable       *sortable,
                                       gint                   sort_column_id,
                                       GtkTreeIterCompareFunc func,
                                       gpointer               data,
                                       GtkDestroyNotify       destroy)
{
    /* FIXME */
}

static void
red_list_model_sortable_set_default_sort_func (GtkTreeSortable       *sortable,
                                               GtkTreeIterCompareFunc func,
                                               gpointer               data,
                                               GtkDestroyNotify       destroy)
{
    /* FIXME */
}

static gboolean
red_list_model_sortable_has_default_sort_func (GtkTreeSortable *sortable)
{
    /* FIXME */
    return FALSE;
}

/* ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** */

static void
red_list_model_clear_columns (RedListModel *model)
{
    int i;

    if (model->columns == NULL)
        return;

    pyg_block_threads ();
    for (i = 0; i < model->columns->len; ++i) {
        RedListModelColumn *col = g_ptr_array_index (model->columns, i);
        Py_DECREF (col->pycallback);
        g_free (col);
    }
    pyg_unblock_threads ();

    g_ptr_array_free (model->columns, TRUE);
    model->columns = NULL;
}

static void
red_list_model_clear_array (RedListModel *model)
{
    int i;

    if (model->array == NULL)
        return;

    pyg_block_threads ();
    for (i = 0; i < model->array->len; ++i) {
        PyObject *obj = g_ptr_array_index (model->array, i);
        Py_DECREF (obj);
    }
    pyg_unblock_threads ();

    g_ptr_array_free (model->array, TRUE);
    model->array = NULL;

    model->index_N = -1;
    g_free (model->index);
    model->index = NULL;
}

/* ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** */

static void
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
    iface->get_path        = red_list_model_get_path;
    iface->get_value       = red_list_model_get_value;
    iface->iter_next       = red_list_model_iter_next;
    iface->iter_children   = red_list_model_iter_children;
    iface->iter_has_child  = red_list_model_iter_has_child;
    iface->iter_n_children = red_list_model_iter_n_children;
    iface->iter_nth_child  = red_list_model_iter_nth_child;
    iface->iter_parent     = red_list_model_iter_parent;
}

static void
red_list_model_sortable_iface_init (GtkTreeSortableIface *iface)
{
    iface->get_sort_column_id    = red_list_model_sortable_get_sort_column_id;
    iface->set_sort_column_id    = red_list_model_sortable_set_sort_column_id;
    iface->set_sort_func         = red_list_model_sortable_set_sort_func;
    iface->set_default_sort_func = red_list_model_sortable_set_default_sort_func;
    iface->has_default_sort_func = red_list_model_sortable_has_default_sort_func;
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

        static const GInterfaceInfo tree_sortable_info = {
            (GInterfaceInitFunc) red_list_model_sortable_iface_init,
            NULL, NULL
        };

        object_type = g_type_register_static (G_TYPE_OBJECT,
                                              "RedListModel",
                                              &object_info, 0);

        g_type_add_interface_static (object_type,
                                     GTK_TYPE_TREE_MODEL,
                                     &tree_model_info);

        g_type_add_interface_static (object_type,
                                     GTK_TYPE_TREE_SORTABLE,
                                     &tree_sortable_info);

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

    pyg_block_threads ();

    N = PyList_Size (pylist);

    if (model->array == NULL)
        model->array = g_ptr_array_new ();

    for (i = 0; i < N; ++i) {
        PyObject *obj = PyList_GET_ITEM (pylist, i);
        Py_INCREF (obj);
        g_ptr_array_add (model->array, obj);
    }

    pyg_unblock_threads ();
}

PyObject *
red_list_model_get_list_item (RedListModel *model,
                              gint          row_num)
{
    g_return_val_if_fail (RED_IS_LIST_MODEL (model), NULL);
    g_return_val_if_fail (model->array, NULL);
    g_return_val_if_fail (row_num >= 0, NULL);

    if (model->index == NULL)
        red_list_model_build_index (model);

    if (model->index != NULL) {
        g_return_val_if_fail (row_num < model->index_N, NULL);
        row_num = model->index[row_num];
    }

    g_return_val_if_fail (row_num < red_list_model_array_length (model), NULL);

    return g_ptr_array_index (model->array, row_num);
}

gint
red_list_model_length (RedListModel *model)
{
    g_return_val_if_fail (RED_IS_LIST_MODEL (model), -1);

    if (model->index == NULL)
        red_list_model_build_index (model);

    if (model->index != NULL)
        return model->index_N;

    return red_list_model_array_length (model);
}

gint
red_list_model_add_column (RedListModel *model,
                           PyObject     *pycallback,
                           GType         type)
{
    RedListModelColumn *col;
    
    g_return_val_if_fail (RED_IS_LIST_MODEL (model), -1);
    g_return_val_if_fail (pycallback != NULL, -1);
    g_return_val_if_fail (PyCallable_Check (pycallback), -1);

    col = g_new0 (RedListModelColumn, 1);
    col->pycallback = pycallback;
    col->type = type;

    pyg_block_threads ();
    Py_INCREF (pycallback);
    pyg_unblock_threads ();

    if (model->columns == NULL)
        model->columns = g_ptr_array_new ();

    g_ptr_array_add (model->columns, col);

    return model->columns->len - 1;
}

void
red_list_model_row_changed (RedListModel *model,
                            gint          row_num)
{
    GtkTreeIter iter;
    GtkTreePath *path;

    g_return_if_fail (RED_IS_LIST_MODEL (model));
    g_return_if_fail (row_num >= 0);
    g_return_if_fail (model->array && row_num < model->array->len);

    ITER_SET_INDEX (&iter, row_num);
    path = gtk_tree_path_new ();
    gtk_tree_path_append_index (path, row_num);

    gtk_tree_model_row_changed (GTK_TREE_MODEL (model), path, &iter);
    
    gtk_tree_path_free (path);
}

void
red_list_model_set_filter_magic (RedListModel *model,
                              PyObject     *filter_callback)
{
    g_return_if_fail (model != NULL);
    g_return_if_fail (filter_callback != NULL);

    g_free (model->index);
    model->index_N = -1;
    model->index = NULL;

    if (filter_callback == Py_None)
        filter_callback = NULL;
    else 
        g_return_if_fail (PyCallable_Check (filter_callback));

    model->filter_callback = filter_callback;
}

void
red_list_model_set_sort_magic (RedListModel *model,
                               PyObject     *sort_callback,
                               gboolean      reverse_sort)
{
    g_return_if_fail (model != NULL);
    g_return_if_fail (sort_callback);

    g_free (model->index);
    model->index_N = -1;
    model->index = NULL;

    if (sort_callback == Py_None)
        sort_callback = NULL;
    else 
        g_return_if_fail (PyCallable_Check (sort_callback));

    model->sort_callback = sort_callback;
    model->reverse_sort  = reverse_sort;
}
