#
# widget_encapsulator.py
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


from gi.repository import Gtk

from labelplus.gtkui import RT
from labelplus.gtkui.common.gtklib import safe_get_name

class WidgetEncapsulator(object):

  def __init__(self, filename, root, attr_prefix=""):

    self._model = None
    self._root_widget = None
    self._widgets = []

    self._attr_prefix = attr_prefix

    self._model = Gtk.Builder.new_from_file(filename)
    if __debug__: RT.register(self._model, __name__)

    self._root_widget = self._model.get_object(root)

    self._widgets = [w for w in self._model.get_objects() if isinstance(w, Gtk.Buildable)]
    for widget in self._widgets:
      if __debug__: RT.register(widget, __name__)

      name = self._attr_prefix + safe_get_name(widget)

      if not hasattr(self, name):
        setattr(self, name, widget)


  @property
  def valid(self):

    return self._root_widget is not None


  def get_widgets(self, prefix=""):

    return [x for x in self._widgets if safe_get_name(x).startswith(prefix)]


  def connect_signals(self, map_):

    if self._model:
      self._model.connect_signals(map_)


  def destroy(self):

    while self._widgets:
      widget = self._widgets.pop()
      name = self._attr_prefix + safe_get_name(widget)

      attr_widget = getattr(self, name, None)
      if attr_widget is widget:
        delattr(self, name)

    if self._root_widget:
      self._root_widget.destroy()
      self._root_widget = None

    self._model = None
