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
"""

import json
import os
import numpy as np

class NPJson(json.JSONEncoder):
  """
  Used to help jsonify numpy arrays or lists that contain numpy data types.
  """
  def default(self, obj):
      if isinstance(obj, np.integer):
          return int(obj)
      elif isinstance(obj, np.floating):
          return float(obj)
      elif isinstance(obj, np.ndarray):
          return obj.tolist()
      else:
          return super(NPJson, self).default(obj)

class _JSONSerializationMixin(object):
  """
  Mixin for json serialization functionalities that are attached to `libraries.logger.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `libraries.logger.Logger`

  In this mixin we can use any attribute/method of the Logger.
  """

  def __init__(self):
    super(_JSONSerializationMixin, self).__init__()
    return

  def load_json(self, 
                fname, 
                folder=None, 
                numeric_keys=True, 
                verbose=True, 
                subfolder_path=None, 
                locking=True):
    assert folder in [None, 'data', 'output', 'models']
    lfld = self.get_target_folder(target=folder)

    if folder is not None:
      if subfolder_path is not None:
        datafile = os.path.join(lfld, subfolder_path.lstrip('/'), fname)
        if verbose:
          self.verbose_log("Loading json '{}' from '{}'/'{}'".format(fname, folder, subfolder_path))
        #endif
      else:
        datafile = os.path.join(lfld, fname)
        if verbose:
          self.verbose_log("Loading json '{}' from '{}'".format(fname, folder))
        #endif
      #endif
    else:
      datafile = fname
      if verbose:
        self.verbose_log("Loading json '{}'".format(fname))
    #endif

    if os.path.isfile(datafile):
      if locking:
        self.lock_resource(datafile) 
      try:
        with open(datafile) as f:
          if not numeric_keys:
            data = json.load(f)
          else:
            data = json.load(f, object_hook=lambda d: {int(k) if k.isnumeric() else k: v for k, v in d.items()})
      except Exception as e:
        self.P("JSON load failed: {}".format(e), color='r')
        data = None
      if locking:
        self.unlock_resource(datafile)
      
      return data
    else:
      if verbose:
        self.verbose_log("  File not found!", color='r')
    return

  @staticmethod
  def safe_dumps_json(dct, **kwargs):
    return json.dumps(dct, cls=NPJson, **kwargs)

  def load_dict(self, **kwargs):
    return self.load_json(**kwargs)

  def load_data_json(self, fname, **kwargs):
    return self.load_json(fname, folder='data', **kwargs)
  
  
  def thread_safe_save(self, datafile, data_json, locking=True):
    if locking:
      self.lock_resource(datafile)
    try:
      with open(datafile, 'w') as fp:
        json.dump(data_json, fp, sort_keys=True, indent=4, cls=NPJson)    
    except:
      pass
    if locking:
      self.unlock_resource(datafile)
    return

    
  def save_data_json(self, 
                     data_json, 
                     fname, 
                     subfolder_path=None, 
                     verbose=True, 
                     locking=True):
    save_dir = self._data_dir
    if subfolder_path is not None:
      save_dir = os.path.join(save_dir, subfolder_path.lstrip('/'))
      os.makedirs(save_dir, exist_ok=True)

    datafile = os.path.join(save_dir, fname)
    if verbose:
      self.verbose_log('Saving data json: {}'.format(datafile))
    self.thread_safe_save(datafile=datafile, data_json=data_json, locking=locking)
    return datafile

  def load_output_json(self, fname, **kwargs):
    return self.load_json(fname, folder='output', **kwargs)

  def save_output_json(self, 
                       data_json, 
                       fname, 
                       subfolder_path=None, 
                       verbose=True, 
                       locking=True):
    save_dir = self._outp_dir
    if subfolder_path is not None:
      save_dir = os.path.join(save_dir, subfolder_path.lstrip('/'))
      os.makedirs(save_dir, exist_ok=True)

    datafile = os.path.join(save_dir, fname)
    if verbose:
      self.verbose_log('Saving output json: {}'.format(datafile))
    self.thread_safe_save(datafile=datafile, data_json=data_json, locking=locking)
    return datafile

  def load_models_json(self, fname, **kwargs):
    return self.load_json(fname, folder='models', **kwargs)

  def save_models_json(self, 
                       data_json, 
                       fname, 
                       subfolder_path=None, 
                       verbose=True, 
                       locking=True):
    save_dir = self._modl_dir
    if subfolder_path is not None:
      save_dir = os.path.join(save_dir, subfolder_path.lstrip('/'))
      os.makedirs(save_dir, exist_ok=True)

    datafile = os.path.join(save_dir, fname)
    if verbose:
      self.verbose_log('Saving models json: {}'.format(datafile))
    self.thread_safe_save(datafile=datafile, data_json=data_json, locking=locking)
    return datafile

  @staticmethod
  def save_json(dct, fname):
    """
    This function is NOT thread safe
    """
    with open(fname, 'w') as fp:
      json.dump(dct, fp, sort_keys=True, indent=4, cls=NPJson)
    return

  def load_dict_from_data(self, fn):
    return self.load_data_json(fn)

  def load_dict_from_models(self, fn):
    return self.load_models_json(fn)

  def load_dict_from_output(self, fn):
    return self.load_output_json(fn)

  @staticmethod
  def save_dict_txt(path, dct):
    json.dump(dct, open(path, 'w'), sort_keys=True, indent=4)
    return

  @staticmethod
  def load_dict_txt(path):
    """
    This function is NOT thread safe
    """
    with open(path) as f:
      data = json.load(f)
    return data
  
  
  def update_data_json(self,
                       fname, 
                       update_callback,
                       subfolder_path=None, 
                       verbose=False,
                       ):
    assert update_callback is not None, "update_callback must be defined!"
    datafile = self.get_file_path(
      fn=fname,
      folder='data',
      subfolder_path=subfolder_path,
      )
    if datafile is None:
      self.P("update_data_json failed due to missing {}".format(datafile), color='error')
      return False
    self.lock_resource(datafile)
    result = None
    try:
      data = self.load_data_json(
        fname=fname,
        verbose=verbose,
        subfolder_path=subfolder_path,
        locking=False,
        )
      
      if data is not None:
        data = update_callback(data)
        
        self.save_data_json(
          data_json=data, 
          fname=fname, 
          verbose=verbose,
          subfolder_path=subfolder_path,
          locking=False,
          )
        result = True
    except Exception as e:
      self.P("update_data_json failed: {}".format(e), color='error')
      result = False
    
    self.unlock_resource(datafile)
    return result
          