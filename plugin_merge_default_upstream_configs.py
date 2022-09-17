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
from copy import deepcopy

# TODO: this should be _ConfigHandlerMixin and should deal with multiple config-related 
# aspects in any config_data using class including LummetryObject !!!
class _PluginMergeDefaultAndUpstreamConfigs(object):

  def __init__(self):
    super(_PluginMergeDefaultAndUpstreamConfigs, self).__init__()
    return

  def _merge_prepare_config(self, default_config=None, delta_config=None, uppercase_keys=True):
    if default_config is None:
      default_config = vars(self).get('_default_config')

    if delta_config is None:
      delta_config = vars(self).get('_upstream_config_params')
      
    if uppercase_keys:
      delta_config = {k.upper():v for k,v in delta_config.items()}
    
    self.P("Updating {} configuration...".format(self.__class__.__name__), color='b')
    if default_config is None:
      self.P("WARNING: no default config was provided at {} startup!".format(
        self.__class__.__name__), color='r')
      final_config = {}
    else:
      final_config = deepcopy(default_config)

    all_keys = set(final_config.keys()).union(set(delta_config.keys()))
    for k in all_keys:
      if final_config.get(k) == delta_config.get(k) or k not in delta_config:
        self.P("  {}={}".format(k, final_config[k]), color='b')
      else:
        if k not in final_config:
          self.P("  {}={} [NEW]".format(k, delta_config[k]), color='m')
        elif final_config[k] != delta_config[k]:
          self.P("  {}={} -> {}={}".format(
            k, final_config[k], k, delta_config[k]),
            color='y')
        final_config[k] = delta_config[k]

    return final_config

  def add_config_data(self, new_config_data):
    if not isinstance(new_config_data, dict):
      self.P("`config_data` must be updated with a dict. Received '{}'".format(type(new_config_data)))
      return False
    
    self.P("Updating '{}' configuration...".format(self.__class__.__name__), color='b')

    all_keys = set(self.config_data.keys()).union(set(new_config_data.keys()))
    for k in all_keys:
      if (self.config_data.get(k) == new_config_data.get(k)) or (k not in new_config_data):
        self.P("  {}={}".format(k, self.config_data[k]), color='b')
      else:
        if k not in self.config_data:
          self.P("  {}={} [NEW]".format(k, new_config_data[k]), color='m')
        elif self.config_data[k] != new_config_data[k]:
          self.P("  {}={} -> {}={}".format(
            k, self.config_data[k], k, new_config_data[k]),
            color='y')
        self.config_data[k] = new_config_data[k]
    return True

  
  def create_config_handlers(self):
    if hasattr(self, 'config_data') and isinstance(self.config_data, dict) and len(self.config_data) > 0:
      for k in self.config_data:
        func_name = 'cfg_' + k.lower()
        if not hasattr(self, func_name):
          fnc = property(fget=lambda self: self.config_data.get(k), doc="Get '{}' from config_data".format(k))
          setattr(self.__class__, func_name, fnc)
    return
  
  
  def run_validation_rules(self):
    result = True
    if (hasattr(self, 'config_data') and 
        isinstance(self.config_data, dict) and 
        self.config_data.get('VALIDATION_RULES') is not None and
        len(self.config_data.get('VALIDATION_RULES')) > 0):
      self.P("Validating configuration for '{}'...".format(self.__class__.__name__))
    else:
      self.P("No validation configuration for '{}'".format(self.__class__.__name__), color='r')
      result = False
    return result
