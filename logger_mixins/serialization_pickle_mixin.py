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

import os
import bz2
import pickle

class _PickleSerializationMixin(object):
  """
  Mixin for pickle serialization functionalities that are attached to `libraries.logger.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `libraries.logger.Logger`

  In this mixin we can use any attribute/method of the Logger.
  """

  def __init__(self):
    super(_PickleSerializationMixin, self).__init__()
    return

  def _save_compressed_pickle(self, full_filename, myobj):
    """
    save object to file using pickle

    @param full_filename: name of destination file
    @param myobj: object to save (has to be pickleable)
    """

    try:
      fhandle = bz2.BZ2File(full_filename, 'wb')
    except:
      self.P('ERROR: File ' + full_filename + ' cannot be written!')
      return False

    pickle.dump(myobj, fhandle, protocol=pickle.HIGHEST_PROTOCOL)
    fhandle.close()
    return True


  def _load_compressed_pickle(self, full_filename):
    """
    Load from filename using pickle

    @param full_filename: name of file to load from
    """

    try:
      fhandle = bz2.BZ2File(full_filename, 'rb')
    except:
      self.P('ERROR: File ' + full_filename + ' cannot be read!')
      return None

    myobj = pickle.load(fhandle)
    fhandle.close()
    return myobj


  def save_pickle(self, data, fn, folder=None,
                  use_prefix=False, verbose=True,
                  compressed=False,
                  subfolder_path=None):
    """
    compressed: True if compression is required OR you can just add '.pklz' to `fn`
    """

    def P(s):
      if verbose:
        self.P(s)
      return

    # enddef

    lfld = self.get_target_folder(target=folder)

    if lfld is None:
      P("Assuming `fn` param ({}) is a full path".format(fn))
      datafile = fn
    else:
      if use_prefix:
        fn = self.file_prefix + '_' + fn
      datafolder = lfld
      if subfolder_path is not None:
        datafolder = os.path.join(datafolder, subfolder_path.lstrip('/'))
        os.makedirs(datafolder, exist_ok=True)
      datafile = os.path.join(datafolder, fn)

    if compressed or '.pklz' in fn:
      if not compressed:
        P("Saving pickle with compression=True forced due to extension")
      else:
        P("Saving pickle with compression...")
      if self._save_compressed_pickle(datafile, myobj=data):
        P("  Compressed pickle {} saved in {}".format(fn, folder))
      else:
        P("  FAILED compressed pickle save!")
    else:
      if subfolder_path is None:
        P("Saving uncompressed pickle {} in '{}'".format(fn, folder))
      else:
        P("Saving uncompressed pickle {} in '{}'/'{}'".format(fn, folder, subfolder_path))
      with open(datafile, 'wb') as fhandle:
        pickle.dump(data, fhandle, protocol=pickle.HIGHEST_PROTOCOL)
      if verbose:
        P("  Saved pickle '{}' in '{}' folder".format(fn, folder))
    return datafile


  def save_pickle_to_data(self, data, fn, compressed=False, verbose=True, subfolder_path=None):
    """
    compressed: True if compression is required OR you can just add '.pklz' to `fn`
    """
    return self.save_pickle(
      data, fn,
      folder='data',
      compressed=compressed,
      subfolder_path=subfolder_path,
      verbose=verbose
    )


  def save_pickle_to_models(self, data, fn, compressed=False, verbose=True, subfolder_path=None):
    """
    compressed: True if compression is required OR you can just add '.pklz' to `fn`
    """
    return self.save_pickle(
      data, fn,
      folder='models',
      compressed=compressed,
      subfolder_path=subfolder_path,
      verbose=verbose
    )


  def save_pickle_to_output(self, data, fn, compressed=False, verbose=True, subfolder_path=None):
    """
    compressed: True if compression is required OR you can just add '.pklz' to `fn`
    """
    return self.save_pickle(
      data, fn,
      folder='output',
      compressed=compressed,
      subfolder_path=subfolder_path,
      verbose=verbose
    )


  def load_pickle_from_models(self, fn, decompress=False, verbose=True, subfolder_path=None):
    """
     decompressed : True if the file was saved with `compressed=True` or you can just use '.pklz'
    """
    return self.load_pickle(
      fn,
      folder='models',
      decompress=decompress,
      verbose=verbose,
      subfolder_path=subfolder_path
    )


  def load_pickle_from_data(self, fn, decompress=False, verbose=True, subfolder_path=None):
    """
     decompressed : True if the file was saved with `compressed=True` or you can just use '.pklz'
    """
    return self.load_pickle(
      fn,
      folder='data',
      decompress=decompress,
      verbose=verbose,
      subfolder_path=subfolder_path
    )


  def load_pickle_from_output(self, fn, decompress=False, verbose=True, subfolder_path=None):
    """
     decompressed : True if the file was saved with `compressed=True` or you can just use '.pklz'
    """
    return self.load_pickle(
      fn,
      folder='output',
      decompress=decompress,
      verbose=verbose,
      subfolder_path=subfolder_path
    )


  def load_pickle(self, fn, folder=None, decompress=False, verbose=True,
                  subfolder_path=None):
    """
     load_from: 'data', 'output', 'models'
     decompressed : True if the file was saved with `compressed=True` or you can just use '.pklz'
    """
    if verbose:
      P = self.P
    else:
      P = lambda x, color=None: x

    lfld = self.get_target_folder(target=folder)

    if lfld is None:
      P("Loading pickle ... Assuming `fn` param ({}) is a full path".format(fn))
      datafile = fn
    else:
      datafolder = lfld
      if subfolder_path is not None:
        datafolder = os.path.join(datafolder, subfolder_path.lstrip('/'))
        P("Loading pickle '{}' from '{}'/'{}'".format(fn, folder, subfolder_path))
      else:
        P("Loading pickle '{}' from '{}'".format(fn, folder))
      datafile = os.path.join(datafolder, fn)

    data = None
    if os.path.isfile(datafile):
      if decompress or '.pklz' in datafile:
        if not decompress:
          P("Loading pickle with decompress=True forced due to extension")
        else:
          P("Loading pickle with decompression...")
        data = self._load_compressed_pickle(datafile)
      else:
        with open(datafile, "rb") as f:
          data = pickle.load(f)
      if data is None:
        P("  Pickle load failed!")
      else:
        P("  Pickle loaded.")
    else:
      P("  File not found! Pickle load failed.", color='r')
    return data