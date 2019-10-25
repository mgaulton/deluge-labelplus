#
# gtkui.py
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


import copy
import datetime
import logging

import twisted.internet.reactor

import deluge.component
import deluge.configmanager

import labelplus.common
import labelplus.common.config
import labelplus.common.label
import labelplus.gtkui.config
import labelplus.gtkui.config.convert
import labelplus.gtkui.common.gtklib.dnd


from twisted.python.failure import Failure

from deluge.ui.client import client
from deluge.plugins.pluginbase import Gtk3PluginBase

from labelplus.common import LabelPlusError
from labelplus.common import serialize_datetime, deserialize_datetime
from labelplus.gtkui.common.label_store import LabelStore
from labelplus.gtkui.extensions.add_torrent_ext import AddTorrentExt
from labelplus.gtkui.extensions.preferences_ext import PreferencesExt
from labelplus.gtkui.extensions.sidebar_ext import SidebarExt
from labelplus.gtkui.extensions.status_bar_ext import StatusBarExt
from labelplus.gtkui.extensions.torrent_view_ext import TorrentViewExt

from labelplus.gtkui import RT


from labelplus.common.literals import (
  STR_UPDATE, ERR_TIMED_OUT, ERR_MAX_RETRY,
)

GTKUI_CONFIG = "%s_ui.conf" % labelplus.common.MODULE_NAME

INIT_POLLING_INTERVAL = 3.0
UPDATE_INTERVAL = 1.0

THROTTLED_INTERVAL = 6.0
MAX_TRIES = 10

REQUEST_TIMEOUT = 10.0

EXTENSIONS = (
  AddTorrentExt,
  PreferencesExt,
  SidebarExt,
  StatusBarExt,
  TorrentViewExt,
)


log = logging.getLogger(__name__)
labelplus.gtkui.common.gtklib.dnd.log.setLevel(logging.INFO)


class GtkUI(Gtk3PluginBase):

  # Section: Initialization

  def __init__(self, plugin_name):

    RT.logger.setLevel(logging.INFO)
    if __debug__: RT.register(self)

    super(GtkUI, self).__init__(plugin_name)

    self.initialized = False

    self.config = None

    self.store = LabelStore()
    self.last_updated = None
    self._tries = 0
    self._calls = []

    self._extensions = []

    self._update_funcs = []
    self._cleanup_funcs = []


  def enable(self):

    log.info("Initializing %s...", self.__class__.__name__)

    self._poll_init()


  def _poll_init(self):

    client.labelplus.is_initialized().addCallback(self._check_init)


  def _check_init(self, result):

    log.debug("Waiting for core to be initialized...")

    if result == True:
      client.labelplus.get_label_updates_dict().addCallback(self._finish_init)
    else:
      twisted.internet.reactor.callLater(INIT_POLLING_INTERVAL,
        self._poll_init)


  def _finish_init(self, result):

    log.debug("Resuming initialization...")

    try:
      info = client.connection_info()
      self.daemon = "%s@%s:%s" % (info[2], info[0], info[1])

      self._load_config()
      self._update_store(result)

      self.initialized = True

      self._load_extensions()

      log.info("%s initialized", self.__class__.__name__)
    except:
      log.error("Error initializing %s", self.__class__.__name__)
      raise

    twisted.internet.reactor.callLater(0, self._update_loop)


  def _load_extensions(self):

    log.info("Loading extensions...")

    for ext in EXTENSIONS:
      try:
        log.debug("Initializing %s", ext.__name__)
        instance = ext(self)
        self._extensions.append(instance)
        if __debug__: RT.register(instance, ext.__name__)
        log.info("%s initialized", ext.__name__)
      except:
        log.exception("Error initializing %s", ext.__name__)


  # Section: Deinitialization

  def disable(self):

    log.info("Deinitializing %s...", self.__class__.__name__)

    labelplus.common.cancel_calls(self._calls)

    self._run_cleanup_funcs()
    self._unload_extensions()
    self._update_funcs = []

    self._close_config()
    self._destroy_store()

    self.initialized = False

    if __debug__: RT.report()

    log.info("%s deinitialized", self.__class__.__name__)


  def _run_cleanup_funcs(self):

    while self._cleanup_funcs:
      func = self._cleanup_funcs.pop()
      try:
        func()
      except:
        log.exception("Failed to run %s()", func.__name__)


  def _unload_extensions(self):

    log.info("Unloading extensions...")

    while self._extensions:
      ext = self._extensions.pop()
      try:
        ext.unload()
        log.info("%s deinitialized", ext.__class__.__name__)
      except:
        log.exception("Error deinitializing %s", ext.__class__.__name__)


  def _destroy_store(self):

    if self.store:
      self.store.destroy()
      self.store = None


  # Section: Public

  def get_extension(self, name):

    for ext in self._extensions:
      if ext.__class__.__name__ == name:
        return ext

    return None


  def register_update_func(self, func):

    if func not in self._update_funcs:
      self._update_funcs.append(func)


  def deregister_update_func(self, func):

    if func in self._update_funcs:
      self._update_funcs.remove(func)


  def register_cleanup_func(self, func):

    if func not in self._cleanup_funcs:
      self._cleanup_funcs.append(func)


  def deregister_cleanup_func(self, func):

    if func in self._cleanup_funcs:
      self._cleanup_funcs.remove(func)


  # Section: Config

  def _load_config(self):

    config = deluge.configmanager.ConfigManager(GTKUI_CONFIG)

    # Workaround for 0.2.19.x that didn't use header
    if config.config.get("version") == 2:
      labelplus.common.config.set_version(config, 2)

    labelplus.common.config.init_config(config,
      labelplus.gtkui.config.CONFIG_DEFAULTS,
      labelplus.gtkui.config.CONFIG_VERSION,
      labelplus.gtkui.config.convert.CONFIG_SPECS)

    self._update_daemon_config(config)
    self._normalize_config(config)

    self.config = config


  def _close_config(self):

    if self.config:
      if self.initialized:
        self.config.save()

      deluge.configmanager.close(GTKUI_CONFIG)


  def _update_daemon_config(self, config):

    saved_daemons = deluge.component.get("ConnectionManager").hostlist.get_hosts_info()
    if not saved_daemons:
      config["daemon"] = {}
    else:
      daemons = ["%s@%s:%s" % (x[3], x[1], x[2]) for x in saved_daemons]

      # Remove daemons from config if not in ConnectionManager hosts
      for daemon in list(config["daemon"].keys()):
        if "@localhost:" in daemon or "@127.0.0.1:" in daemon:
          continue

        if daemon not in daemons and daemon != self.daemon:
          del config["daemon"][daemon]

    if self.daemon not in config["daemon"]:
      config["daemon"][self.daemon] = copy.deepcopy(
        labelplus.gtkui.config.DAEMON_DEFAULTS)


  def _normalize_config(self, config):

    labelplus.common.normalize_dict(config.config,
      labelplus.gtkui.config.CONFIG_DEFAULTS)

    labelplus.common.normalize_dict(config["common"],
      labelplus.gtkui.config.CONFIG_DEFAULTS["common"])

    for daemon in config["daemon"]:
      labelplus.common.normalize_dict(config["daemon"][daemon],
        labelplus.gtkui.config.DAEMON_DEFAULTS)


  # Section: Update

  def _update_loop(self):

    def on_timeout():

      log.error("%s: %s", STR_UPDATE, LabelPlusError(ERR_TIMED_OUT))

      if self.initialized:
        self._tries += 1
        if self._tries < MAX_TRIES:
          self._calls.append(twisted.internet.reactor.callLater(
            THROTTLED_INTERVAL, self._update_loop))
        else:
          log.error("%s: %s", STR_UPDATE, LabelPlusError(ERR_MAX_RETRY))


    def process_result(result):

      if isinstance(result, Failure):
        if failure.check(LabelPlusError):
          log.error("%s: %s", STR_UPDATE, LabelPlusError(result.value.message))
          interval = THROTTLED_INTERVAL
        else:
          return result
      else:
        self._tries = 0
        interval = UPDATE_INTERVAL
        self._update_store(result)

      if self.initialized:
        self._calls.append(twisted.internet.reactor.callLater(interval,
          self._update_loop))


    labelplus.common.clean_calls(self._calls)

    if self.initialized:
      iso_time = serialize_datetime(self.last_updated)
      deferred = client.labelplus.get_label_updates_dict(iso_time)
      labelplus.common.deferred_timeout(deferred, REQUEST_TIMEOUT, on_timeout,
        process_result, process_result)


  def _update_store(self, result):

    if not result:
      return

    update = result

    log.debug("Update: Type: %s, Timestamp: %s", update['type'],
      update['timestamp'])

    self.last_updated = deserialize_datetime(update['timestamp'])
    self.store.update(update['data'])

    for func in list(self._update_funcs):
      try:
        func(self.store)
      except:
        log.exception("Failed to run %s()", func.__name__)
