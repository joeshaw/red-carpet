/* -*- Mode: C; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */

/*
 * redlistview.c
 *
 * Copyright (C) 2002 Ximian, Inc.
 *
 * Developed by Jon Trowbridge <trow@ximian.com>
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
#include "redlistview.h"

typedef struct _RedListViewSpanner RedListViewSpanner;
struct _RedListViewSpanner {
    int      row;
    int      col0, col1;
    GtkCellRenderer *cell;

    gboolean draw_bg;
    GdkColor bg_color;
};

static GObjectClass *parent_class = NULL;

/* ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** */

static void
red_list_view_spanner_free (RedListViewSpanner *spanner)
{
    if (spanner) {
        g_object_unref (spanner->cell);
        g_free (spanner);
    }
}

/* ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** */

static void
red_list_view_finalize (GObject *obj)
{
    RedListView *view = RED_LIST_VIEW (obj);
    GSList *iter;

    for (iter = view->spanners; iter != NULL; iter = iter->next) {
        RedListViewSpanner *spanner = iter->data;
        red_list_view_spanner_free (spanner);
    }
    g_slist_free (view->spanners);

    if (parent_class->finalize)
        parent_class->finalize (obj);
}

static gboolean
red_list_view_find_row_rectangle (RedListView *view,
                                  int          row,
                                  GdkRectangle *rect)
{
    GtkTreePath *path;
    GList *cols;
    GtkTreeViewColumn *col0;
    GtkTreeViewColumn *col1;
    GdkRectangle rect0, rect1;

    path = gtk_tree_path_new ();
    gtk_tree_path_append_index (path, row);

    cols = gtk_tree_view_get_columns (GTK_TREE_VIEW (view));
    col0 = GTK_TREE_VIEW_COLUMN (cols->data);
    col1 = GTK_TREE_VIEW_COLUMN (g_list_last (cols)->data);
    g_list_free (cols);

    gtk_tree_view_get_background_area (GTK_TREE_VIEW (view),
                                       path,
                                       col0,
                                       &rect0);

    gtk_tree_view_get_background_area (GTK_TREE_VIEW (view),
                                       path,
                                       col1,
                                       &rect1);

    rect->x = rect0.x;
    rect->y = rect1.y;
    rect->height = rect0.height;
    rect->width = rect1.x + rect1.width - rect0.x;
    
    gtk_tree_path_free (path);

    return TRUE;
}

static void
combine_rectangles (GdkRectangle *dst,
                    GdkRectangle *src1,
                    GdkRectangle *src2)
{
    dst->x = src1->x;
    dst->y = src1->y;
    dst->width = src2->x + src2->width - src1->x;
    dst->height = src1->height;
}

static void
red_list_view_paint_spanners (RedListView    *view,
                              GdkWindow      *window,
                              GdkEventExpose *ev)
{
    GSList *iter;
    GdkRectangle rect0, rect1, cell_area, bg_area;
    GtkTreeViewColumn *col0, *col1;
    GtkTreePath *path;
    GdkGC *gc;

    gc = gdk_gc_new (window);

    for (iter = view->spanners; iter != NULL; iter = iter->next) {
        RedListViewSpanner *spanner = iter->data;
        
        col0 = gtk_tree_view_get_column (GTK_TREE_VIEW (view), spanner->col0);
        col1 = gtk_tree_view_get_column (GTK_TREE_VIEW (view), spanner->col1);

        path = gtk_tree_path_new ();
        gtk_tree_path_append_index (path, spanner->row);
            
        gtk_tree_view_get_background_area (GTK_TREE_VIEW (view), path, col0, &rect0);
        gtk_tree_view_get_background_area (GTK_TREE_VIEW (view), path, col1, &rect1);
        combine_rectangles (&bg_area, &rect0, &rect1);

        gtk_tree_view_get_cell_area (GTK_TREE_VIEW (view), path, col0, &rect0);
        gtk_tree_view_get_cell_area (GTK_TREE_VIEW (view), path, col1, &rect1);
        combine_rectangles (&cell_area, &rect0, &rect1);

        if (spanner->draw_bg) {
            gdk_gc_set_foreground (gc, &spanner->bg_color);
            gdk_draw_rectangle (window, gc, TRUE,
                                bg_area.x, bg_area.y,
                                bg_area.width, bg_area.height);
        }

        if (spanner->cell) {
            gtk_cell_renderer_render (spanner->cell, window, GTK_WIDGET (view),
                                      &bg_area, &cell_area, &ev->area, 0);
        }

        gtk_tree_path_free (path);
    }

    gdk_gc_unref (gc);
}

static gboolean
red_list_view_expose_event (GtkWidget      *w,
                            GdkEventExpose *ev)
{
    GdkWindow *win;
    gboolean rv;
    
    if (GTK_WIDGET_CLASS (parent_class)->expose_event)
        rv = GTK_WIDGET_CLASS (parent_class)->expose_event (w, ev);

    /* We need to check to make sure that the expose event is actually
       occuring on the window where the table data is being drawn.  If
       we don't do this check, row zero spanners can be drawn on top
       of the column headers. */
    win = gtk_tree_view_get_bin_window (GTK_TREE_VIEW (w));
    if (win == ev->window)
        red_list_view_paint_spanners (RED_LIST_VIEW (w), win, ev);

    return rv;
}
                            

static void
red_list_view_class_init (RedListViewClass *klass)
{
    GObjectClass *obj_class = (GObjectClass *) klass;
    GtkWidgetClass *widget_class = (GtkWidgetClass *) klass;

    parent_class = g_type_class_peek_parent (klass);

    obj_class->finalize = red_list_view_finalize;

    widget_class->expose_event = red_list_view_expose_event;
}

static void
red_list_view_init (RedListView *view)
{

}

GType
red_list_view_get_type (void)
{
    static GType object_type = 0;

    if (! object_type) {

        static const GTypeInfo object_info = {
            sizeof (RedListViewClass),
            NULL, NULL,
            (GClassInitFunc) red_list_view_class_init,
            NULL, NULL,
            sizeof (RedListView),
            0,
            (GInstanceInitFunc) red_list_view_init
        };

        object_type = g_type_register_static (GTK_TYPE_TREE_VIEW,
                                              "RedListView",
                                              &object_info, 0);
    }

    return object_type;
}

RedListView *
red_list_view_new (void)
{
    return RED_LIST_VIEW (g_object_new (RED_TYPE_LIST_VIEW, NULL));
}

/* ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** */

void
red_list_view_add_spanner_with_background (RedListView *view,
                                           gint row, gint col0, gint col1,
                                           GtkCellRenderer *cell,
                                           GdkColor *bg_color)
{
    RedListViewSpanner *spanner;
    GdkColormap *colormap;

    g_return_if_fail (RED_IS_LIST_VIEW (view));
    g_return_if_fail (cell == NULL || GTK_IS_CELL_RENDERER (cell));

    if (col0 < 0 || col1 < 0) {
        /* Why don't they just have a gtk_tree_view_get_n_columns method? */
        GList *cols = gtk_tree_view_get_columns (GTK_TREE_VIEW (view));
        gint N = g_list_length (cols);
        g_list_free (cols);
        if (col0 < 0)
            col0 += N;
        if (col1 < 0)
            col1 += N;
    }

    spanner = g_new0 (RedListViewSpanner, 1);
    spanner->row = row;
    spanner->col0 = col0;
    spanner->col1 = col1;
    spanner->cell = g_object_ref (cell);
    spanner->draw_bg = (bg_color != NULL);
    if (bg_color) {
        spanner->bg_color = *bg_color;
        colormap = gtk_widget_get_colormap (GTK_WIDGET (view));
        gdk_colormap_alloc_color (colormap, &spanner->bg_color, TRUE, TRUE);
    }

    view->spanners = g_slist_append (view->spanners, spanner);
}

void
red_list_view_add_spanner (RedListView *view,
                           gint row, gint col0, gint col1,
                           GtkCellRenderer *cell)
{
    red_list_view_add_spanner_with_background (view, row, col0, col1, cell, NULL);
}
