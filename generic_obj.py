# -*- coding: utf-8 -*-
"""
Created on Thu Jul 25 09:17:02 2019

@author: Andrei
"""

import json
  
__VER__ = '0.2.0.3' 

class LummetryObject:
  """
  Generic class
  
  Instructions:
      
    1. use `super().__init__(**kwargs)` at the end of child `__init__`
    2. define `startup(self)` method for the child class and call 
       `super().startup()` at beginning of `startup()` method
  
  """
  def __init__(self, log, DEBUG=False, show_prefixes=False,
               prefix_log=None, **kwargs):
    
    if (log is None) or not hasattr(log, '_logger'):
      raise ValueError("Loggger object is invalid: {}".format(log))
      
    self.log = log
    self._base_object_ver = __VER__
    self.show_prefixes = show_prefixes
    self.prefix_log = prefix_log
    self.config_data = self.log.config_data
    self.DEBUG = DEBUG
    self.sess = None
    self.session = None
    if not hasattr(self, '__name__'):
      self.__name__ = 'LummetryBaseClass'
    self.startup()
    
    return
  

  def _parse_config_data(self, *args, **kwargs):
    """
    args: keys that are used to prune the config_data. Examples:
                1. args=['TEST'] -> kwargs will be searched in
                                    log.config_data['TEST']
                2. args=['TEST', 'K1'] -> kwargs will be searched in
                                          log.config_data['TEST']['K1']
    kwargs: dictionary of k:v pairs where k is a parameter and v is its value.
            If v is None, then k will be searched in logger config data in order to set
            the value specified in json.
            Finally, the method will set the final value to a class attribute named 
            exactly like the key.
    """
    cfg = self.log.config_data
    for x in args:
      if x is not None:
        cfg = cfg[x]

    for k,v in kwargs.items():
      if v is None and k in cfg:
        v = cfg[k]

      setattr(self, k, v)

    return


  def startup(self):
    self.log.set_nice_prints()
    ver = ''
    if hasattr(self,'__version__'):
      ver = 'v.' + self.__version__
    if hasattr(self,'version'):
      ver = 'v.' + self.version
      
    self.P("{} {} startup.".format(self.__class__.__name__, ver))
    return

  def shutdown(self):
    self.P("Shutdown in progress...")
    if self.sess is not None:
      self.P(" Closing tf-session...")
      self.sess.close()
      self.P(" tf-session closed.")
    if self.session is not None:
      self.P(" Closing tf-session...")
      self.sess.close()
      self.P(" tf-session closed.")
    return


  def P(self, s, t=False):    
    if self.show_prefixes:
      _r = self.log.P("{}: {}".format(
                self.__name__,s),show_time=t)
    else:
      if self.prefix_log is None:
        _r = self.log.P("{}".format(s),show_time=t)
      else:
        _r = self.log.P("{} {}".format(self.prefix_log, s), show_time=t)
    return _r
        
  
  def D(self, s, t=False):
    _r = -1
    if self.DEBUG:
      if self.show_prefixes:
        _r = self.log.P("[DEBUG] {}: {}".format(
                        self.__name__,s),show_time=t)
      else:
        if self.prefix_log is None:
          _r = self.log.P("[D] {}".format(s),show_time=t)      
        else:
          _r = self.log.P("[D]{} {}".format(self.prefix_log, s), show_time=t)
    return _r
  
  
  def start_timer(self, tmr_id):    
    return self.log.start_timer(sname=self.__name__ + '_' + tmr_id)
  
  
  def end_timer(self, tmr_id, skip_first_timing=True):
    return self.log.end_timer(sname=self.__name__ + '_' + tmr_id,
                              skip_first_timing=skip_first_timing)

  def SaveJSON(self, json_data, fname):
    if self.output_local:
      with open(fname, 'w') as f:
        json.dump(json_data, f, sort_keys=True, indent=4)
    else:
      self.log.save_output_json(json_data, fname)


  def _run(self, _call, _output, feed_dict):    
    if self.sess is None:
      raise ValueError("Called `_run` however session object `self.sess` is not initialized!")
    if (_call not in self.first_run.keys()) or (not self.first_run[_call]):
      self.first_run[_call] = False
      self.D("Call: {}  Output: {}   Input: {}".format(_call, _output, feed_dict))
    self.log.start_timer(_call)
    res = self.sess.run(_output,feed_dict=feed_dict)
    self.log.end_timer(_call,skip_first_timing=False)
    return res
  
  
  def raise_error(self, error_text):
    """
    logs the error and raises it
    """
    self.P("{}: {}".format(self.__class__.__name__, error_text))
    raise ValueError(error_text)
  
  
