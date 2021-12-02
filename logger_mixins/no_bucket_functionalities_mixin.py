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
"""

import os
import itertools
import sys
import pickle
import hashlib
import numpy as np

from io import BytesIO, TextIOWrapper

class _NoBucketFunctionalitiesMixin(object):
  """
  Mixin for functionalities that do not belong to any mixin that are attached to `libraries.logger.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `libraries.logger.Logger`

  In this mixin we can use any attribute/method of the Logger.
  """

  def __init__(self):
    super(_NoBucketFunctionalitiesMixin, self).__init__()

  @staticmethod
  def get_function_parameters(function):
    import inspect
    signature = inspect.signature(function)
    parameters = signature.parameters

    all_params = []
    required_params = []
    optional_params = []

    for k, v in parameters.items():
      if k == 'self':
        continue

      all_params.append(k)

      if v.default is inspect._empty:
        required_params.append(k)
      else:
        optional_params.append(k)

    return all_params, required_params, optional_params

  @staticmethod
  def string_diff(seq1, seq2):
    return sum(1 for a, b in zip(seq1, seq2) if a != b) + abs(len(seq1) - len(seq2))

  @staticmethod
  def flatten_2d_list(lst):
    return list(itertools.chain.from_iterable(lst))

  @staticmethod
  def get_obj_size(obj, seen=None):
    """Recursively finds size of objects"""
    size = sys.getsizeof(obj)
    if seen is None:
      seen = set()
    obj_id = id(obj)
    if obj_id in seen:
      return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(obj, dict):
      size += sum([_NoBucketFunctionalitiesMixin.get_obj_size(v, seen) for v in obj.values()])
      size += sum([_NoBucketFunctionalitiesMixin.get_obj_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
      size += _NoBucketFunctionalitiesMixin.get_obj_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
      size += sum([_NoBucketFunctionalitiesMixin.get_obj_size(i, seen) for i in obj])

    return size

  @staticmethod
  def find_documentation(class_name, *args):
    # setup the environment
    old_stdout = sys.stdout
    sys.stdout = TextIOWrapper(BytesIO(), sys.stdout.encoding)
    # write to stdout or stdout.buffer
    help(class_name)
    # get output
    sys.stdout.seek(0)  # jump to the start
    out = sys.stdout.read()  # read output
    # restore stdout
    sys.stdout.close()
    sys.stdout = old_stdout

    out_splitted = out.split('\n')
    filtered_doc = list(filter(lambda x: all([_str in x for _str in args]),
                               out_splitted))

    return filtered_doc

  @staticmethod
  def common_start(*args):
    """ returns the longest common substring from the beginning of passed `args` """

    def _iter():
      for t in zip(*args):
        s = set(t)
        if len(s) == 1:
          yield list(s)[0]
        else:
          return

    return ''.join(_iter())

  @staticmethod
  def distance_euclidean(np_x, np_y):
    return np.sqrt(np.sum((np_x - np_y) ** 2, axis=1))

  @staticmethod
  def code_version(lst_dirs=['.'], lst_exclude=[]):
    import re
    import pandas as pd
    from pandas.util import hash_pandas_object
    from pathlib import Path

    assert len(lst_dirs) > 0
    assert all([os.path.isdir(x) for x in lst_dirs])
    assert all([os.path.isdir(x) for x in lst_exclude])
    dct_temp = {}
    dct = {'FILE': [], 'VER': []}
    for d in lst_dirs:
      for orig_file in Path(d).rglob('**/*.py'):
        try:
          orig_file = str(orig_file)
          if any([x in orig_file for x in lst_exclude]):
            continue
          # endif
          file = orig_file
          file_ver = '{}_ver'.format(re.sub(r'[^\w\s]', '', file))
          for x in ['/', '\\']:
            file = file.replace(x, '.')
          file = file.replace('.py', '')
          for key in ['__version__', '__VER__']:
            try:
              cmd = 'from {} import {} as {}'.format(file, key, file_ver)
              exec(cmd, dct_temp)
            except:
              pass
              # endfor

          if file_ver in dct_temp:
            dct['FILE'].append(orig_file)
            dct['VER'].append(dct_temp[file_ver])
          # endif
        except Exception as e:
          pass
      # endfor
    # endfor
    df = pd.DataFrame(dct).sort_values('FILE').reset_index(drop=True)
    return df, hex(hash_pandas_object(df).sum())

  @staticmethod
  def natural_sort(l):
    import re
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key=alphanum_key)

  @staticmethod
  def hash_object(obj):
    """
    Uses md5 to get the hash of any pickleable object

    Parameters:
    -----------
    obj : any pickleable object, mandatory

    Returns:
    ---------
    md5 hash : str

    """
    p = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
    return hashlib.md5(p).hexdigest()
