#
# __init__.py
#
# Copyright (C) 2014 Ratanak Lun <ratanakvlun@gmail.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Linking this software with other modules is making a combined work
# based on this software. Thus, the terms and conditions of the GNU
# General Public License cover the whole combination.
#
# As a special exception, the copyright holders of this software give
# you permission to link this software with independent modules to
# produce a combined work, regardless of the license terms of these
# independent modules, and to copy and distribute the resulting work
# under terms of your choice, provided that you also meet, for each
# linked module in the combined work, the terms and conditions of the
# license of that module. An independent module is a module which is
# not derived from or based on this software. If you modify this
# software, you may extend this exception to your version of the
# software, but you are not obligated to do so. If you do not wish to
# do so, delete this exception statement from your version.
#


from gi.repository import Gtk, Gdk

from labelplus.gtkui import RT


def textview_set_text(textview, text):

  buff = textview.get_buffer()
  buff.set_text(text)
  textview.set_buffer(buff)


def textview_get_text(textview):

  buff = textview.get_buffer()

  return buff.get_text(buff.get_start_iter(), buff.get_end_iter())


def liststore_create(types, rows):

  if not isinstance(types, (list, tuple)):
    types = (types,)

  ls = Gtk.ListStore(*types)

  for values in rows:
    if not isinstance(values, (list, tuple)):
      values = (values,)

    ls.append(values)

  return ls


def treemodel_get_children(model, iter_=None):

  if iter_:
    return [x.iter for x in model[iter_].iterchildren()]
  else:
    return [x.iter for x in model]


def menu_add_items(menu, pos, specs, *args):

  menu_items = []

  if pos < 0:
    pos = -len(specs)

  for spec in specs:
    schematic = spec[0]
    if len(schematic) > 1:
      item = schematic[0](**schematic[1])
    else:
      item = schematic[0]()

    if __debug__: RT.register(item, __name__)

    if len(spec) > 1 and spec[1]:
      item.connect("activate", *(tuple(spec[1:])+args))

    menu_items.append(item)
    menu.insert(item, pos)
    pos += 1

  return menu_items


def menu_add_separator(menu, pos=-1):

  sep = Gtk.SeparatorMenuItem()
  menu.insert(sep, pos)

  if __debug__: RT.register(sep, __name__)

  return sep


def widget_print_tree(widget, indent, step):

  if hasattr(widget, "get_title"):
    extra = widget.get_title()
  elif hasattr(widget, "get_label"):
    extra = widget.get_label()
  elif hasattr(widget, "get_text"):
    extra = widget.get_text()
  else:
    extra = ""

  print((" "*(indent*step), widget, extra))

  if isinstance(widget, Gtk.Container):
    for child in widget.get_children():
      widget_print_tree(child, indent+1, step)

  if isinstance(widget, Gtk.TreeView):
    for col in widget.get_columns():
      widget_print_tree(col, indent+1, step)


def widget_get_descendents(widget, types=(), count=-1):

  def get_descendents(widget, types, descendents, count):

    if count != -1 and len(descendents) >= count:
      return

    if not isinstance(widget, Gtk.Container):
      return

    for child in widget.get_children():
      if not types or type(child) in types:
        descendents.append(child)

      get_descendents(child, types, descendents, count)


  descendents = []
  get_descendents(widget, types, descendents, count)

  return descendents


class ImageMenuItem(Gtk.MenuItem):

  def __init__(self, stock_id=None, label=None, use_underline=True):

    super(ImageMenuItem, self).__init__()

    self._box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 4)
    self._box.set_halign(Gtk.Align.START)
    self.add(self._box)

    if stock_id is not None:
      self._image = Gtk.Image.new_from_icon_name(stock_id,  Gtk.IconSize.MENU)
      self._box.pack_start(self._image, True, True, 0)

    if label is not None:
      self._label = Gtk.Label.new_with_mnemonic(label)
      self._label.set_mnemonic_widget(self)
      self._box.pack_start(self._label, True, True, 0)

    self.set_use_underline(use_underline)

def safe_get_name(widget):
  if isinstance(widget, Gtk.Buildable):
    n = Gtk.Buildable.get_name(widget)
    if n is not None:
      return n

  return widget.get_name()
