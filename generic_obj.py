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
from datetime import datetime as dt

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
               log_at_startup=False,
               **kwargs):

    super(LummetryObject, self).__init__()

    if (log is None) or not hasattr(log, '_logger'):
      raise ValueError("Loggger object is invalid: {}".format(log))
      
    self.log = log
    self.show_prefixes = show_prefixes
    self.prefix_log = prefix_log
    self.config_data = self.log.config_data
    self.DEBUG = DEBUG
    self.log_at_startup = log_at_startup

    self._messages = deque(maxlen=maxlen_notifications)

    if not hasattr(self, '__name__'):
      self.__name__ = self.__class__.__name__
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

    if self.log_at_startup:
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
      msg = "[{}]: {}".format(self.__name__, s)
    else:
      if self.prefix_log is None:
        msg = "{}".format(s)
      else:
        msg = "{} {}".format(self.prefix_log, s)
      #endif
    #endif

    _r = self.log.P(msg, show_time=t, color=color)
    return _r

  def D(self, s, t=False):
    _r = -1
    if self.DEBUG:
      if self.show_prefixes:
        msg = "[DEBUG] {}: {}".format(self.__name__,s)
      else:
        if self.prefix_log is None:
          msg = "[D] {}".format(s)
        else:
          msg = "[D]{} {}".format(self.prefix_log, s)
        #endif
      #endif
      _r = self.log.P(msg, show_time=t, color='yellow')
    #endif
    return _r

  def start_timer(self, tmr_id):
    return self.log.start_timer(sname=self.__name__ + '_' + tmr_id)

  def end_timer(self, tmr_id, skip_first_timing=True):
    return self.log.end_timer(
      sname=self.__name__ + '_' + tmr_id,
      skip_first_timing=skip_first_timing
    )

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

  def _create_notification(self, notification_type, notification, **kwargs):
    message = {
      'MODULE': self.__class__.__name__
    }

    if hasattr(self, '__version__'):
      message['VERSION'] = self.__version__

    message['NOTIFICATION_TYPE'] = notification_type
    message['NOTIFICATION'] = notification
    message['TIMESTAMP'] = self.log.now_str(nice_print=True, short=False)
    message = {**message, **kwargs}
    self._messages.append(message)
    return

  def get_notifications(self):
    lst = []
    while len(self._messages) > 0:
      lst.append(self._messages.popleft())
    return lst
  
  
  def get_cmd_handlers(self, update=False):
    if hasattr(self, 'COMMANDS') and isinstance(getattr(self, 'COMMANDS'), dict):
      COMMANDS = self.COMMANDS.copy()
    else:
      COMMANDS = {}
    for k in dir(self):
      if k.startswith('cmd_handler_'):
        cmd = k.replace('cmd_handler_', '').upper()
        if cmd not in COMMANDS:
          COMMANDS[cmd] = getattr(self, k)
    if update:
      self.COMMANDS = COMMANDS
    return COMMANDS


  def run_cmd(self, cmd, **kwargs):
    res = None
    cmd = cmd.upper()
    dct_cmds = self.get_cmd_handlers()
    if cmd in dct_cmds:
      func = dct_cmds[cmd]
      res = func(**kwargs)
    else:
      print("Received unk command '{}'".format(cmd))
    return res
