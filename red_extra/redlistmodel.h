/* -*- Mode: C; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */

/*
 * redlistmodel.h
 *
 * Copyright (C) 2002-2003 Ximian, Inc.
 *
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

#ifndef __REDLISTMODEL_H__
#define __REDLISTMODEL_H__

#define NO_IMPORT_PYGOBJECT
#include <Python.h>
#include "pygobject.h"
#include <gtk/gtk.h>

typedef struct _RedListModelColumn RedListModelColumn;
typedef struct _RedListModel       RedListModel;
typedef struct _RedListModelClass  RedListModelClass;

struct _RedListModelColumn {
    PyObject *pycallback;
    GType type;
};

struct _RedListModel {
    GObject parent_instance;

    GPtrArray *columns;
    GPtrArray *array;

    gint index_N;
    gint *index;

    PyObject *filter_callback;
    PyObject *sort_callback;
    gboolean  reverse_sort;
};

struct _RedListModelClass {
    GObjectClass parent_class;
};

#define RED_TYPE_LIST_MODEL            (red_list_model_get_type())
#define RED_LIST_MODEL(obj)            (G_TYPE_CHECK_INSTANCE_CAST((obj), RED_TYPE_LIST_MODEL, RedListModel))
#define RED_LIST_MODEL_CLASS(klass)    (G_TYPE_CHECK_CLASS_CAST((obj), RED_TYPE_LIST_MODEL, RedListModelClass))
#define RED_IS_LIST_MODEL(obj)         (G_TYPE_CHECK_INSTANCE_TYPE((obj), RED_TYPE_LIST_MODEL))
#define RED_IS_LIST_MODEL_CLASS(klass) (G_TYPE_CHECK_CLASS_TYPE((klass), RED_TYPE_LIST_MODEL))
#define RED_LIST_MODEL_GET_CLASS(obj)  (G_TYPE_INSTANCE_GET_CLASS((obj), RED_TYPE_LIST_MODEL, RedListModelClass))

GType         red_list_model_get_type         (void);

RedListModel *red_list_model_new              (void);

void          red_list_model_set_list         (RedListModel *model,
                                               PyObject     *pylist);

PyObject     *red_list_model_get_list_item    (RedListModel *model,
                                               gint          row_num);

gint          red_list_model_length           (RedListModel *model);

gint          red_list_model_add_column       (RedListModel *model,
                                               PyObject     *pycallback,
                                               GType         type);

void          red_list_model_row_changed      (RedListModel *model,
                                               gint          row_num);

void          red_list_model_set_filter_magic (RedListModel *model,
                                               PyObject     *filter_callback);

void          red_list_model_set_sort_magic   (RedListModel *model,
                                               PyObject     *sort_callback,
                                               gboolean      reverse_sort);

#endif /* __REDLISTMODEL_H__ */

