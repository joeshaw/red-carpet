/* -*- Mode: C; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */

/*
 * redlistview.h
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

#ifndef __REDLISTVIEW_H__
#define __REDLISTVIEW_H__

#include <Python.h>
#include "pygobject.h"
#include <gtk/gtk.h>

typedef struct _RedListView        RedListView;
typedef struct _RedListViewClass   RedListViewClass;

struct _RedListView {
    GtkTreeView parent_instance;

    GSList *spanners;
};

struct _RedListViewClass {
    GtkTreeViewClass parent_class;
};

#define RED_TYPE_LIST_VIEW            (red_list_view_get_type())
#define RED_LIST_VIEW(obj)            (G_TYPE_CHECK_INSTANCE_CAST((obj), RED_TYPE_LIST_VIEW, RedListView))
#define RED_LIST_VIEW_CLASS(klass)    (G_TYPE_CHECK_CLASS_CAST((obj), RED_TYPE_LIST_VIEW, RedListViewClass))
#define RED_IS_LIST_VIEW(obj)         (G_TYPE_CHECK_INSTANCE_TYPE((obj), RED_TYPE_LIST_VIEW))
#define RED_IS_LIST_VIEW_CLASS(klass) (G_TYPE_CHECK_CLASS_TYPE((klass), RED_TYPE_LIST_VIEW))
#define RED_LIST_VIEW_GET_CLASS(obj)  (G_TYPE_INSTANCE_GET_CLASS((obj), RED_TYPE_LIST_VIEW, RedListViewClass))

GType red_list_view_get_type (void);

RedListView *red_list_view_new (void);

void red_list_view_add_spanner_with_background (RedListView *view,
                                                gint row, int col0, int col1,
                                                GtkCellRenderer *cell,
                                                GdkColor *bg_color);

void red_list_view_add_spanner (RedListView *view,
                                gint row, int col0, int col1,
                                GtkCellRenderer *cell);
                                
                                


#endif /* __REDLISTVIEW_H__ */

