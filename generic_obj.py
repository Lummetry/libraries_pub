# -*- coding: utf-8 -*-
"""
Copyright 2019 Lummetry.AI (Knowledge Investment Group SRL). All Rights Reserved.


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
"""


from libraries import Logger
from collections import deque

__VER__ = '0.2.0.2'

class LummetryObject(object):
  """
  Generic class
  
  Instructions:
      
    1. use `super().__init__(**kwargs)` at the end of child `__init__`
    2. define `startup(self)` method for the child class and call 
       `super().startup()` at beginning of `startup()` method
       
      OR
      
    use `super().__init__(**kwargs)` at beginning of child `__init__` and then
    you can safely proceed with other initilization 
  
  """
  def __init__(self, log : Logger,
               DEBUG=False,
               show_prefixes=False,
               prefix_log=None,
               maxlen_notifications=None,
               **kwargs):

    super(LummetryObject, self).__init__()

    if (log is None) or not hasattr(log, '_logger'):
      raise ValueError("Loggger object is invalid: {}".format(log))
      
    self.log = log
    self._base_object_ver = __VER__
    self.show_prefixes = show_prefixes
    self.prefix_log = prefix_log
    self.config_data = self.log.config_data
    self.DEBUG = DEBUG

    self._messages = deque(maxlen=maxlen_notifications)

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
      
    self.P("{}{} startup.".format(self.__class__.__name__, ' ' + ver if ver != '' else ''))
    return

  def shutdown(self):
    self.P("Shutdown in progress...")
    _VARS = ['sess', 'session']
    for var_name in _VARS:
      if vars(self).get(var_name, None) is not None:
        self.P("Warning: {} property {} still not none before closing".format(
          self.__class__.__name__, var_name), color='r')
    return


  def P(self, s, t=False, color=None, prefix=False):    
    if self.show_prefixes or prefix:
      _r = self.log.P("[{}]: {}".format(
                self.__name__,s),show_time=t, color=color)
    else:
      if self.prefix_log is None:
        _r = self.log.P("{}".format(s),show_time=t, color=color)
      else:
        _r = self.log.P("{} {}".format(self.prefix_log, s), show_time=t, color=color)
    return _r
        
  
  def D(self, s, t=False):
    _r = -1
    if self.DEBUG:
      if self.show_prefixes:
        _r = self.log.P("[DEBUG] {}: {}".format(
                        self.__name__,s),show_time=t, color='yellow')
      else:
        if self.prefix_log is None:
          _r = self.log.P("[D] {}".format(s),show_time=t, color='yellow')      
        else:
          _r = self.log.P("[D]{} {}".format(self.prefix_log, s), show_time=t, color='yellow')
    return _r
  
  
  def start_timer(self, tmr_id):    
    return self.log.start_timer(sname=self.__name__ + '_' + tmr_id)
  
  
  def end_timer(self, tmr_id, skip_first_timing=True):
    return self.log.end_timer(sname=self.__name__ + '_' + tmr_id,
                              skip_first_timing=skip_first_timing)

  
  def raise_error(self, error_text):
    """
    logs the error and raises it
    """
    self.P("{}: {}".format(self.__class__.__name__, error_text))
    raise ValueError(error_text)
  
  def timer_name(self, name=''):
    tn = ''
    if name == '':
      tn = self.__class__.__name__
    else:
      tn = '{}__{}'.format(self.__class__.__name__, name)
    return tn

  def _create_notification(self, notification_type, notification):
    message = {
      'MODULE': self.__class__.__name__
    }

    if hasattr(self, '__version__'):
      message['VERSION'] = self.__version__

    message['NOTIFICATION_TYPE'] = notification_type
    message['NOTIFICATION'] = notification
    self._messages.append(message)
    return

  def get_notifications(self):
    lst = []
    while len(self._messages) > 0:
      lst.append(self._messages.popleft())
    return lst
  
  
if __name__ == '__main__':
  class Test(LummetryObject):
    def __init__(self, **kwargs):
      self.sess = 'BlaBla'
      super().__init__(**kwargs)

      
    
  
