# -*- coding: utf-8 -*-
"""
Copyright 2019-2021 Lummetry.AI (Knowledge Investment Group SRL). All Rights Reserved.


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
@created on: Fri Sep 16 09:08:23 2022
@created by: AID
"""
import zlib
import sys
import base64

__VER__ = '0.4.0'

UNALLOWED_DICT = {
  'import '        : 'Imports are not allowed in plugin code',
  'globals'       : 'Global vars access is not allowed in plugin code',
  'locals'        : 'Local vars dict access is not allowed in plugin code',
  'memoryview'    : 'Pointer handling is unsafe in plugin code',
  'self.log.'     : 'Logger object cannot be used directly in plugin code - please use API',
  'vars('        : 'Usage of `vars(obj)` not allowed in plugin code',
  'dir('         : 'Usage of `dir(obj)` not allowed in plugin code',
  
}

class BaseCodeChecker:
  """
  This class should be used either as a associated object for code checking or
  as a mixin for running code
  """
  def __init__(self):
    super(BaseCodeChecker, self).__init__()
    return
  
  def __msg(self, m, color='w'):
    if hasattr(self, 'log'):
      self.log.P(m, color=color)
    else:
      print(m)
    return
  
  def _preprocess_code(self, code):
    res = ''
    in_string = False
    for c in code:
      if c == '"':
        if not in_string:
          in_string = True
        else:
          in_string = False

      if c == "'":
        if not in_string:
          in_string = True
        else:
          in_string = False
      
      if c == '\n' and in_string:
        res += '\\n'
      else:
        res += c
    return res

  def _check_unsafe_code(self, code):
    errors = {}
    lst_lines = code.splitlines()
    for line, _line in enumerate(lst_lines):
      # strip any lead and trail whitespace
      str_line = _line.strip()
      if len(str_line) == 0 or str_line[0] == '#':
        # if line is comment then skip it
        continue
      for fault in UNALLOWED_DICT:
        # lets check each possible fault for current line
        if (
            str_line.startswith(fault) or  # start with fault
            (' ' + fault) in str_line or   # contains a fault with a space before
            ('\t' + fault) in str_line or  # contains the fault with the tab before
            (',' + fault) in str_line or   # contains the fault with a leading comma
            (';' + fault) in str_line      # contains the fault with a leading ;
            ):
          msg = UNALLOWED_DICT[fault]
          if msg not in errors:
            errors[msg] = []
          errors[msg].append(line)
    if len(errors) == 0:
      return None
    else:
      return errors
    
  ###### PUB
  
  
  def check_code_text(self, code):
    return self._check_unsafe_code(code)
    
  
  def code_to_base64(self, code, verbose=True, compress=True):   
    if verbose:
      self.__msg("Processing:\n{}".format(code), color='y')
    errors = self._check_unsafe_code(code)
    if errors is not None:
      self.__msg("Cannot serialize code due to: '{}'".format(errors), color='r')
      return None
    l_i = len(code)
    l_c = -1
    b_code = bytes(code, 'utf-8')    
    if compress:
      b_code = zlib.compress(b_code, level=9)
      l_c = sys.getsizeof(b_code)
    b_encoded = base64.b64encode(b_code)
    str_encoded = b_encoded.decode('utf-8')
    l_b64 = len(str_encoded)
    self.__msg("Code checking and serialization suceeded. Initial/Compress/B64: {}/{}/{}".format(
      l_i, l_c, l_b64), color='g'
    )
    return str_encoded
  
  
  def base64_to_code(self, b64code, decompress=True):
    decoded = None
    try:
      b_decoded = base64.b64decode(b64code)
      if decompress:
        b_decoded = zlib.decompress(b_decoded)
      s_decoded = b_decoded.decode('utf-8')
      decoded = s_decoded
    except:
      pass
    return decoded
  
    
  def prepare_b64code(self, str_b64code, check_for_result=True):
    errors = None
    code = None
    code = self.base64_to_code(str_b64code)
    errors = self._check_unsafe_code(code)
    if errors is None:
      if code is None:
        errors = 'Provided ascii data is not a valid base64 object'
      elif check_for_result and '__result' not in code:
        errors = 'No `__result` variable is set'
    if errors is None:
      code = self._preprocess_code(code)
    return code, errors
    
  
  def exec_code(self, str_b64code, debug=False):
    code, errors = self.prepare_b64code(str_b64code)
    if errors is not None:
      self.__msg("Cannot execute remote code: {}".format(errors), color='r')
      result = None
    else:
      if debug:
        self.__msg("Executing: \n{}".format(code))
      exec(code)    
      result = locals().get('__result')
    return result, errors



