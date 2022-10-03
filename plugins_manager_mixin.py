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

from .code_cheker.base_code_checker import BaseCodeChecker

class _PluginsManagerMixin:

  def __init__(self):
    super(_PluginsManagerMixin, self).__init__()
    self.code_checker = BaseCodeChecker()
    return

  def _get_avail_plugins(self, locations):
    if not isinstance(locations, list):
      locations = [locations]

    names, modules = [], []
    for plugins_location in locations:
      path = plugins_location.replace('.', '/')
      files = [os.path.splitext(x)[0] for x in os.listdir(path) if '.py' in x and '__init__' not in x]
      modules += [plugins_location + '.' + x for x in files]
      names += [x.replace('_', '').lower() for x in files]

    return names, modules

  def _get_plugin_by_name(self, lst_plugins_locations, name):
    name = name.lower()
    names, modules = self._get_avail_plugins(lst_plugins_locations)
    if name in names:
      idx = names.index(name)
      return modules[idx]

    return
  
  def _perform_module_safety_check(self, module):
    good = True
    msg = ''
    str_code = inspect.getsource(module)
    self.P("  Performing code safety check on module {}:".format(module.__name__), color='m')
    ### TODO: finish code analysis using BaseCodeChecker
    errors = self.code_checker.check_code_text(str_code)
    if errors is not None:      
      msg = "  ERROR: Unsafe code in {}:\n{}".format(
        module.__name__, '\n'.join(
          ['  *** ' +msg + 'at line(s): {}'.format(v) for msg, v in errors.items()]
          ))
      self.P(msg, color='error')
      self.P("   ********* In future this will STOP the usage of this plugin. **************", color='r')
      # now set good = False
    # endif bad code
    self.P("  Finished performing code safety check on module {}:".format(module.__name__), color='m')
    return good, msg

  def _perform_class_safety_check(self, classdef):
    good = True
    msg = ''
    str_code = inspect.getsource(classdef)
    self.P("Performing code safety check on class {}:".format(classdef.__name__), color='m')
    ### TODO: finish code analysis using BaseCodeChecker
    return good, msg

  def _get_module_name_and_class(self, locations, name, suffix=None, verbose=1, safety_check=False, safe_locations=None):
    if not isinstance(locations, list):
      locations = [locations]

    _class_name, _cls_def, _config_dict = None, None, None
    simple_name = name.replace('_','')

    if suffix is None:
      suffix = ''

    suffix = suffix.replace('_', '')
    
    _safe_module_name = None
    is_safe_plugin = False
    # first search is safe locations always!
    if safe_locations is not None and isinstance(safe_locations, list) and len(safe_locations) > 0:
      _safe_module_name = self._get_plugin_by_name(safe_locations, simple_name)
    if _safe_module_name is None:
      _user_module_name = self._get_plugin_by_name(locations, simple_name)
      _module_name = _user_module_name
    else:
      is_safe_plugin = True 
      _module_name = _safe_module_name
    
    
    if _module_name is None:
      if verbose >= 1:
        self.P("Error with finding plugin '{}' in locations '{}'".format(simple_name, locations), color='r')
      return _module_name, _class_name, _cls_def, _config_dict

    self.P("  Found {} plugin '{}'".format(
      'safe' if is_safe_plugin else 'user', name), 
      color='g' if is_safe_plugin else 'm'
    )
    
    safety_check = False if is_safe_plugin else safety_check

    try:
      module = importlib.import_module(_module_name)
      if module is not None and safety_check:
        is_good, msg = self._perform_module_safety_check(module)
        if not is_good:
          raise ValueError("Unsafe code exception: {}".format(msg))
      classes = inspect.getmembers(module, inspect.isclass)
      for _cls in classes:
        if _cls[0].upper() == simple_name.upper() + suffix.upper():
          _class_name, _cls_def = _cls
      if _class_name is None:
        if verbose >= 1:
          self.P("ERROR: Could not find class match for {}. Available classes are: {}".format(
            simple_name, [x[0] for x in classes]
          ), color='r')
      _config_dict = getattr(module, "_CONFIG", None)
      if _cls_def is not None and safety_check:
        is_good, msg = self._perform_class_safety_check(_cls_def)
        if not is_good:
          raise ValueError("Unsafe class code exception: {}".format(msg))     
      _found_location = ".".join(_module_name.split('.')[:-1])
      self.P("  Plugin '{}' loaded and checked from {}".format(name, _found_location), color='g')
    except:
      str_err = traceback.format_exc()
      msg = "Error preparing {} with module {}:\n{}".format(
        name, _module_name, str_err)
      self.P(msg, color='error')

    return _module_name, _class_name, _cls_def, _config_dict
