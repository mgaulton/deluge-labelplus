#
# convert.py
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


from labelplus.gtkui.config import (
  CONFIG_DEFAULTS_V2,
  CONFIG_DEFAULTS_V3,
  CONFIG_DEFAULTS_V4,
)


def post_map_v2_v3(spec, dict_in):

  for daemon in dict_in["daemon"]:
    state = dict_in["daemon"][daemon]["sidebar_state"]

    if not isinstance(state["selected"], list):
      state["selected"] = [state["selected"]]

    for i, id_ in enumerate(state["selected"]):
      if id_.startswith("-"):
        state["selected"][i] = id_.partition(":")[2]

    for i, id_ in enumerate(state["expanded"]):
      if id_.startswith("-"):
        state["expanded"][i] = id_.partition(":")[2]

  return dict_in


CONFIG_SPEC_V1_V2 = {
  "version_in": 1,
  "version_out": 2,
  "defaults": CONFIG_DEFAULTS_V2,
  "strict": False,
  "deepcopy": False,
  "map": {
    "name_input_size": "common/name_input_size",
    "name_input_pos": "common/name_input_pos",
    "label_options_size": "common/label_options_size",
    "label_options_pos": "common/label_options_pos",

    "prefs_state": "common/prefs_state",

    "show_label_bandwidth": "common/show_label_bandwidth",
  },
}

CONFIG_SPEC_V2_V3 = {
  "version_in": 2,
  "version_out": 3,
  "defaults": CONFIG_DEFAULTS_V3,
  "strict": True,
  "deepcopy": False,
  "post_func": post_map_v2_v3,
  "map": {
    "common/name_input_size": "common/name_input_size",
    "common/name_input_pos": "common/name_input_pos",
    "common/label_options_size": "common/label_options_size",
    "common/label_options_pos": "common/label_options_pos",

    "common/prefs_state": "common/prefs_state",

    "common/show_label_bandwidth": "common/status_bar",
    "common/status_include_sublabel": "common/status_bar_include_sublabels",

    "daemon": "daemon",
  },
}

CONFIG_SPEC_V3_V4 = {
  "version_in": 3,
  "version_out": 4,
  "defaults": CONFIG_DEFAULTS_V4,
  "strict": False,
  "deepcopy": False,
  "map": { "*": "*" },
}

CONFIG_SPECS = {
  (1, 2): CONFIG_SPEC_V1_V2,
  (2, 3): CONFIG_SPEC_V2_V3,
  (3, 4): CONFIG_SPEC_V3_V4,
}
