"""
Copyright 2019-2022 Lummetry.AI (Knowledge Investment Group SRL). All Rights Reserved.


* NOTICE:  All information contained herein is, and remains
* the property of Knowledge Investment Group SRL.  
* The intellectual and technical concepts contained
* herein are proprietary to Knowledge Investment Group SRL
* and may be covered by Romanian and Foreign Patents,
* patents in process, and are protected by trade secret or copyright law.
* Dissemination of this information or reproduction of this material
* is strictly forbidden unless prior written permission is obtained
* from Knowledge Investment Group SRL.


@copyright: Lummetry.AI
@author: Lummetry.AI - Laurentiu
@project: 
@description:
"""

import os
import inspect
import importlib
import traceback

class _PluginsManagerMixin:

  def __init__(self):
    super(_PluginsManagerMixin, self).__init__()
    return

  def _get_avail_plugins(self, locations):
    if not isinstance(locations, list):
      locations = [locations]

    names, modules = [], []
    for plugins_location in locations:
      path = plugins_location.replace('.', '/')
      files = [os.path.splitext(x)[0] for x in os.listdir(path) if '.py' in x]
      modules += [plugins_location + '.' + x for x in files]
      names += [x.replace('__local__', '').replace('_', '').lower() for x in files]

    return names, modules

  def _get_plugin_by_name(self, lst_plugins_locations, name):
    name = name.lower()
    names, modules = self._get_avail_plugins(lst_plugins_locations)
    if name in names:
      idx = names.index(name)
      return modules[idx]

    return

  def _get_module_name_and_class(self, locations, name, suffix=None, verbose=1):
    if not isinstance(locations, list):
      locations = [locations]

    _class_name, _cls_def, _config_dict = None, None, None
    simple_name = name.replace('_','')

    if suffix is None:
      suffix = ''

    suffix = suffix.replace('_', '')

    _module_name = self._get_plugin_by_name(locations, simple_name)
    if _module_name is None:
      if verbose >= 1:
        self.P("Error with finding plugin '{}' in locations '{}'".format(simple_name, locations))
      return _module_name, _class_name, _cls_def, _config_dict

    try:
      module = importlib.import_module(_module_name)
      classes = inspect.getmembers(module, inspect.isclass)
      for _cls in classes:
        if _cls[0].upper() == simple_name.upper() + suffix.upper():
          _class_name, _cls_def = _cls
      if _class_name is None:
        if verbose >= 1:
          self.P("ERROR: Could not find class match for {}. Available classes are: {}".format(
            simple_name, [x[0] for x in classes]
          ))
      _config_dict = getattr(module, "_CONFIG", None)
    except:
      str_err = traceback.format_exc()
      if verbose >= 1:
        self.P("Error preparing {} with module {}:\n{}".format(
          name, _module_name, str_err
        ))

    return _module_name, _class_name, _cls_def, _config_dict
