#!/usr/bin/env python
#
# Ross Burton <ross@burtonini.com>
# Dafydd Harries <daf@rhydd.org>
#
# PyGTK Version by:
#  Thomas Wood <thos@gnome.org>
#
# Copyright 2009 Intel Corporation
# Copyright 2005 Ross Burton
# Copyright 2005 Dafydd Harries
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Template text is Public Domain

import os
import gtk
import re

PACKAGE_NAME    = "GTypeInterface Generator"
PACKAGE_VERSION = "0.1"
PACKAGE_AUTHORS = ["Jesus Barbero Rodriguez"]
PACKAGE_COPYRIGHT = "Copyright 2009 Jesus Barbero Rodriguez"

# TODO:\
# toggle for property skeletons
# signals

h_template = """\
/* %(filename)s.h */

#ifndef %(header_guard)s
#define %(header_guard)s 

#include <glib-object.h>

G_BEGIN_DECLS

#define %(package_upper)s_TYPE_%(object_upper)s %(class_lower)s_get_type()

#define %(package_upper)s_%(object_upper)s(obj) \\
  (G_TYPE_CHECK_INSTANCE_CAST ((obj), \\
  %(package_upper)s_TYPE_%(object_upper)s, %(class_camel)s))

#define %(package_upper)s_IS_%(object_upper)s(obj) \\
  (G_TYPE_CHECK_INSTANCE_TYPE ((obj), \\
  %(package_upper)s_TYPE_%(object_upper)s))

#define %(package_upper)s_%(object_upper)s_GET_INTERFACE(obj) \\
  (G_TYPE_INSTANCE_GET_INTERFACE ((obj), \\
  %(package_upper)s_TYPE_%(object_upper)s, %(class_camel)sInterface))


typedef struct _%(class_camel)s               %(class_camel)s; /* dummy object */
typedef struct _%(class_camel)sInterface      %(class_camel)sInterface;

struct _%(class_camel)sInterface
{
  GTypeInterface parent_iface;

  void (*do_action) (%(class_camel)s *self);
};

GType %(class_lower)s_get_type (void);

void %(class_lower)s_do_action (%(class_camel)s *self);

G_END_DECLS

#endif /* %(header_guard)s */
"""

c_template = """\
/* %(filename)s.c */

#include "%(filename)s.h"

static void
%(class_lower)s_base_init (gpointer g_class)
{
  static gboolean is_initialized = FALSE;

  if (!is_initialized)
    {
      /* add properties and signals to the interface here */

      is_initialized = TRUE;
    }
}

GType
%(class_lower)s_get_type (void)
{
  static GType iface_type = 0;
  if (iface_type == 0)
    {
      static const GTypeInfo info = {
        sizeof (%(class_camel)sInterface),
        %(class_lower)s_base_init,   /* base_init */
        NULL,   /* base_finalize */
      };

      iface_type = g_type_register_static (G_TYPE_INTERFACE, "%(class_camel)s",
                                           &info, 0);
    }

  return iface_type;
}

void
%(class_lower)s_do_action (%(class_camel)s *self)
{
  g_return_if_fail (%(package_upper)s_IS_%(object_upper)s (self));

  %(package_upper)s_%(object_upper)s_GET_INTERFACE (self)->do_action (self);
}
"""

def make_class_init(data):
    lines = [
        'static void',
        '%(class_lower)s_class_init (%(class_camel)sClass *klass)',
        '{'
        ]

    lines.append('}')
    return ''.join([line % data + '\n' for line in lines])

def handle_post(button, ui):
    string_keys = ("class_camel", "class_lower", "package_upper",
                   "object_upper", "parent", "parent_camel");
    data = {}


    for key in string_keys:
        # TODO: sanity check against nulls
        data[key] = ui.get_object (key).get_text()

    if (data['class_lower'] == ''):
      dlg = gtk.MessageDialog (ui.get_object ("main-window"), gtk.DIALOG_MODAL,
                               gtk.MESSAGE_ERROR, gtk.BUTTONS_OK)
      dlg.set_markup ("No class name specified!")
      dlg.run ()
      dlg.destroy ()
      return

    data['filename'] = data['class_lower'].replace('_', "-")
    data['class_init'] = make_class_init(data).strip()
    data['header_guard'] = "_" + data['filename'].upper().replace('.', '_').replace('-', '_') + "_H"
    extra = []

    data['extra'] = '\n'.join([x % data for x in extra])

    select_folder = gtk.FileChooserDialog(title="Select Destination",
                                    action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                    buttons=(gtk.STOCK_CANCEL,
                                    gtk.RESPONSE_CANCEL,
                                    gtk.STOCK_OPEN,
                                    gtk.RESPONSE_ACCEPT))
    if select_folder.run() == gtk.RESPONSE_ACCEPT:
        folder = select_folder.get_filename() + "/"
    else:
        folder = ""
    select_folder.destroy()
    if folder == "":
        return

    f = open (folder + data['filename'] + '.h', 'w')
    f.write (h_template % data)

    f = open (folder + data['filename'] + '.c', 'w')
    f.write (c_template % data)

def guess_class_params (entry, ui):

    text = entry.get_text()
    m = re.findall ('[A-Z]+[a-z]*', text)
    if (m):
      s = m[0]
    else:
      s = ''
    ui.get_object ('package_upper').set_text (s.upper())

    if (m and len(m) > 1):
      s = m[1]
      i = 2
      while (i < len(m)):
        s = s + "_" + m[i]
        i = i + 1
    else:
       s = ''

    ui.get_object ('object_upper').set_text (s.upper())

    if (m):
      s = m[0]
      i = 1
      while (i < len(m)):
        s = s + "_" + m[i]
        i = i + 1
    else:
      s = ''

    ui.get_object ('class_lower').set_text (s.lower())

def guess_parent_params (entry, ui):

    text = entry.get_text()

    # special case GObject
    if (text == 'GObject'):
      s = 'G_TYPE_OBJECT'
    else:
      m = re.findall ('[A-Z]+[a-z]*', text)
      s = ''
      if (m):
        s = m[0] + '_TYPE'
        if (len(m) > 1):
          i = 1
          while (i < len(m)):
            s = s + "_" + m[i]
            i = i + 1

    ui.get_object ('parent').set_text (s.upper())


def about_button_clicked_cb (button, ui):
    about = gtk.AboutDialog()
    about.set_transient_for (ui.get_object ('main-window'))
    about.set_name (PACKAGE_NAME)
    about.set_version (PACKAGE_VERSION)
    about.set_authors (PACKAGE_AUTHORS)
    about.set_copyright (PACKAGE_COPYRIGHT);
    about.set_license ("""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
                       """)
    about.set_comments ("Generates GObjects from the given parameters")
    about.set_logo_icon_name ("applications-development")
    about.run ()
    about.destroy ()


ui = gtk.Builder()
ui.add_from_file ("gifaceui.xml")

window = ui.get_object ('main-window')
window.show_all()
window.connect ('delete-event', gtk.main_quit);

button = ui.get_object ('save-button')
button.connect ('clicked', handle_post, ui)

button = ui.get_object ('about-button')
button.connect ('clicked', about_button_clicked_cb, ui)

ui.get_object ('class_camel').connect ('changed', guess_class_params, ui)
ui.get_object ('parent_camel').connect ('changed', guess_parent_params, ui)

gtk.main()

