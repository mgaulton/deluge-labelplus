#
# autolabel_box.py
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


import labelplus.gtkui.common.gtklib


from labelplus.gtkui.common.gtklib.criteria_box import CriteriaBox

from labelplus.common import _
from labelplus.gtkui import RT


from labelplus.common.config.autolabel import (
  PROPS, OPS, CASES,
  FIELD_PROP, FIELD_OP, FIELD_CASE, FIELD_QUERY,
)


class AutolabelBox(CriteriaBox):

  def __init__(self, homogeneous=False, row_spacing=0, column_spacing=0):

    super(AutolabelBox, self).__init__(homogeneous, row_spacing,
      column_spacing)

    prop_store = labelplus.gtkui.common.gtklib.liststore_create(str,
      [_(x) for x in PROPS])
    op_store = labelplus.gtkui.common.gtklib.liststore_create(str,
      [_(x) for x in OPS])
    case_store = labelplus.gtkui.common.gtklib.liststore_create(str,
      [_(x) for x in CASES])

    if __debug__: RT.register(prop_store, __name__)
    if __debug__: RT.register(op_store, __name__)
    if __debug__: RT.register(case_store, __name__)

    self.add_combobox_column(prop_store)
    self.add_combobox_column(op_store)
    self.add_combobox_column(case_store)
    self.add_entry_column(expand=True)

    # Determine minimum width
    row = self.add_row()
    self.show()
    min_size, size = self.get_preferred_size()
    self.remove(row)
    self.set_size_request(size.width, -1)


  def get_all_row_values(self):

    rows = super(AutolabelBox, self).get_all_row_values()

    for i, row in enumerate(rows):
      row[FIELD_PROP] = PROPS[row[FIELD_PROP]]
      row[FIELD_OP] = OPS[row[FIELD_OP]]
      row[FIELD_CASE] = CASES[row[FIELD_CASE]]
      try:
        row[FIELD_QUERY] = str(row[FIELD_QUERY], "utf8")
      except (TypeError, UnicodeDecodeError):
        pass

      rows[i] = tuple(row)

    return tuple(rows)


  def set_all_row_values(self, rows):

    converted_rows = []

    for row in rows:
      row = list(row)

      row[FIELD_PROP] = PROPS.index(row[FIELD_PROP])
      row[FIELD_OP] = OPS.index(row[FIELD_OP])
      row[FIELD_CASE] = CASES.index(row[FIELD_CASE])

      converted_rows.append(row)

    super(AutolabelBox, self).set_all_row_values(converted_rows)
