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

class _PluginMergeDefaultAndUpstreamConfigs(object):

  def __init__(self):
    super(_PluginMergeDefaultAndUpstreamConfigs, self).__init__()
    return

  def _merge_prepare_config(self, default_config=None, delta_config=None):
    if default_config is None:
      default_config = self._default_config

    if delta_config is None:
      delta_config = self._upstream_config_params

    self.P("Praparing {} configuration...".format(self.__class__.__name__), color='b')
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
