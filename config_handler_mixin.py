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
@author: Lummetry.AI 
@project: 
@description:
  

TODO:
  aspects in any config_data using class including LummetryObject !!!
  as a rule-of-the-thumb this mixin should be used as:
    - add_config_data(dct_config) - this will append/update new config to the config_data
    - create_config_handlers - after we have final config_data we can create implicit `cfg_` handlers
    - validation  & run_validation_rules - finally check if all is ok
  
  
"""
from copy import deepcopy

class CONST:
  RULES = 'VALIDATION_RULES'
  TYPE = 'TYPE'
  FUNC = '_cfg_validate_'
  MIN_VAL = 'MIN_VAL'
  MAX_VAL = 'MAX_VAL'
  MIN_LEN = 'MIN_LEN'
  EXCLUDED_LIST = 'EXCLUDED_LIST'
  

from functools import partial
def getter(slf, obj=None, key=None):
  return obj.config_data.get(key)

class _ConfigHandlerMixin(object):

  def __init__(self):
    super(_ConfigHandlerMixin, self).__init__()
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
      res = []
      for k in self.config_data:
        func_name = 'cfg_' + k.lower()
        if not hasattr(self, func_name):
          # below is a bit tricky: using a lambda generates a non-deterministic abnormal behavior
          # the ideea is to create a global func instance that wil be then loaded on the class (not instance)
          # as a descriptor object - ie a `property`. "many Bothans died to bring the plans of the Death Star..."
          fnc = partial(getter, obj=self, key=k) # create the func
          cls = type(self) # get the class
          fnc_prop = property(fget=fnc, doc="Get '{}' from config_data".format(k)) # create prop from func 
          setattr(cls, func_name, fnc_prop) # set the prop of the class
          res.append(func_name)
      if len(res) > 0:
        self.P("Created '{}' config_data handlers: {}".format(self.__class__.__name__, res), color='b')
    return
  
  
  def _cfg_check_type(self, cfg_key, types):
    val = self.config_data.get(cfg_key)
    if not isinstance(val, types):
      msg = "'{}' config key '{}={}' requires type {} ".format(
        self.__class__.__name__, cfg_key, val, types,
      )
      return False, msg
    return True, ''
  
  def _cfg_check_min_max(self, cfg_key, dct_rules):
    res = True
    msg = None
    _min = dct_rules.get(CONST.MIN_VAL)
    _max = dct_rules.get(CONST.MAX_VAL)
    val = self.config_data.get(cfg_key)
    if _min is not None and val < _min:
      msg = "'{}' config key '{}={}' of type {} requires value > {}".format(
        self.__class__.__name__, cfg_key, val, dct_rules.get(CONST.TYPE), _min,
      )
      return False, msg
    
    if _max is not None and val > _max:
      msg = "'{}' config key '{}={}' of type {} requires value < {}".format(
        self.__class__.__name__, cfg_key, val, dct_rules.get(CONST.TYPE),  _max,
      )
      return False, msg
    return res, msg

  def _cfg_check_exclusions(self, cfg_key, dct_rules):
    _excl_lst = dct_rules.get(CONST.EXCLUDED_LIST)
    val = self.config_data.get(cfg_key)
    if _excl_lst is not None and val in _excl_lst:
      msg = "'{}' config key '{}={}' found in exclutions {}".format(
        self.__class__.__name__, cfg_key, val, _excl_lst,
      )
      return False, msg
    return True, ''

  
  def _cfg_validate_int(self, cfg_key, dct_rules):
    res1, msg1 = self._cfg_check_type(cfg_key=cfg_key, types=(int,))
    res2, msg2 = self._cfg_check_min_max(cfg_key=cfg_key, dct_rules=dct_rules)
    res = res1 and res2      
    msg = msg1 if not res1 else msg2
    return res, msg
  
  def _cfg_validate_float(self, cfg_key, dct_rules):    
    res1, msg1 = self._cfg_check_type(cfg_key=cfg_key, types=(int,float))
    res2, msg2 = self._cfg_check_min_max(cfg_key=cfg_key, dct_rules=dct_rules)
    res = res1 and res2      
    msg = msg1 if not res1 else msg2
    return res, msg
  
  
  def _cfg_validate_str(self, cfg_key, dct_rules):
    res1, msg1 = self._cfg_check_type(cfg_key=cfg_key, types=(str,))
    res2, msg2 = self._cfg_check_exclusions(cfg_key=cfg_key, dct_rules=dct_rules)

    msg3 = None
    val = self.config_data.get(cfg_key)
    _min_len = dct_rules.get(CONST.MIN_LEN, 0)
    if _min_len is not None and len(val) < _min_len:
      msg3 = "'{}' config key '{}={}' of type {} must have at least {} chars".format(
        self.__class__.__name__, cfg_key, val, dct_rules.get(CONST.TYPE), _min_len,
      )
      res3 = False
    res = res1 and res2 and res3
    msg = msg1 if not res1 else (msg2 if not res2 else msg3)
    return res, msg      
    
    
  
  def run_validation_rules(self):
    result = True
    self.P("Validating configuration for '{}'...".format(self.__class__.__name__), color='b')
    if (hasattr(self, 'config_data') and 
        isinstance(self.config_data, dict) and 
        self.config_data.get(CONST.RULES) is not None and
        len(self.config_data.get(CONST.RULES)) > 0):
      dct_validation = self.config_data.get(CONST.RULES)
      for k in dct_validation:
        # run each config key present in validation area
        if k not in self.config_data:
          self.P("  Key '{}' found in validation is not present in config_data", color='r')
          continue
        dct_rules = dct_validation.get(k, {})
        if len(dct_rules) > 0:
          # now we get the actual type of the value 
          str_type= dct_rules.get(CONST.TYPE)
          if isinstance(str_type, str) and len(str_type) > 1:
            try:
              _type = eval(str_type)
            except:
              self.P("  TYPE '{}' pre-validation failed!".format(str_type))
              _type = None
          else:
            self.P("  No TYPE information found for '{}'".format(k), color='r')       
          if False:
            self.P("  Processing key '{}' of type '{}'".format(k, _type.__name__))#DELETE
          if _type in [int, float, str, dict, list]:
            # create validation function out of this mixin available funcs
            str_func = CONST.FUNC + _type.__name__
            func = getattr(self, str_func, None)
            res = True # assume good
            if func is None:
              # if we use a predefined type then we must have the validation
              self.P("  No handler for '{}' config key validation".format(_type.__name__), color='r')
              # maybe we can put res = False here?
            else:
              msg = ''
              # now we run the validation function
              res = func(k, dct_rules)
              if isinstance(res, tuple):
                res, msg = res
            # end run-or-fail validation
            if not res:
              # validation failed
              self.P("  Config validation for '{}={}' of '{}' failed: {}".format(
                k, self.config_data.get(k), self.__class__.__name__, msg),
                color='r'
              )
              result = False
              # here we can break for but we leave to see what other error we have 
          else:
            self.P("  Unavailable handler for type '{}' for '{}'".format(_type, k), color='r')
            if _type is not None:
              # but we can still run the 
              res, msg = self._cfg_check_type(cfg_key=k, types=_type)
              if not res:
                self.P("  Automatic checking of unhandled type '{}' for '{}' failed on data: {}".format(
                  _type, k, self.config_data.get(k)),
                  color='r'
                )
        else:
          self.P("  Empty rules info for '{}'".format(k))
        # end if rules parsing
      # end for each key validation 
      self.P("  Validation for '{}' is {}successful".format(
        self.__class__.__name__, '' if result else 'NOT ',
      ), color='g' if result else 'r')
    else:
      self.P("  No validation configuration for '{}'".format(self.__class__.__name__), color='r')
      result = False
    return result
