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
import sys

from datetime import datetime as dt
from io import BytesIO, TextIOWrapper

class _DataFrameMixin(object):
  """
  Mixin for dataframe functionalities that are attached to `libraries.libraries.libraries.logger.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `libraries.libraries.logger.Logger`

  In this mixin we can use any attribute/method of the Logger.
  """

  def __init__(self):
    super(_DataFrameMixin, self).__init__()
    return

  def load_dataframe(self,
                     fn, timestamps=None, folder='data', subfolder_path=None):
    """
    if fn ends in ".zip" then the loading will also uncompress in-memory
    """
    import pandas as pd

    assert folder in [None, 'data', 'output', 'models']
    lfld = self.get_target_folder(target=folder)

    if folder is not None:
      datafolder = lfld
      if subfolder_path is not None:
        datafolder = os.path.join(datafolder, subfolder_path.lstrip('/'))
        self.verbose_log("Loading CSV '{}' from '{}'/'{}'".format(fn, folder, subfolder_path))
      else:
        self.verbose_log("Loading CSV '{}' from '{}'".format(fn, folder))
      datafile = os.path.join(datafolder, fn)
    else:
      datafile = fn
      self.verbose_log("Loading CSV '{}'".format(fn))

    ext = os.path.splitext(datafile)[-1]
    file_path = datafile

    self.P("Loading dataframe '{}'...".format(datafile))

    if not os.path.exists(file_path):
      self.P("  Dataframe not found.")
      return

    if ext.lower() == '.zip':
      df = pd.read_pickle(file_path)
    else:
      if timestamps is not None:
        if type(timestamps) is str:
          timestamps = [timestamps]
        df = pd.read_csv(file_path, parse_dates=timestamps)
      else:
        df = pd.read_csv(file_path)
    return df

  def load_output_dataframe(self,
                            fn, timestamps=None):
    """
    if fn ends in ".zip" then the loading will also uncompress in-memory
    """
    import pandas as pd

    ext = os.path.splitext(fn)[-1]
    file_path = os.path.join(self._outp_dir, fn)
    self.P("Loading '{}'...".format(file_path))
    if ext.lower() == '.zip':
      df = pd.read_pickle(file_path)
    else:
      if timestamps is not None:
        if type(timestamps) is str:
          timestamps = [timestamps]
        df = pd.read_csv(file_path, parse_dates=timestamps)
      else:
        df = pd.read_csv(file_path)
    return df

  def load_abs_dataframe(self,
                         fn, timestamps=None):
    """
    if fn ends in ".zip" then the loading will also uncompress in-memory
    """
    import pandas as pd

    ext = os.path.splitext(fn)[-1]
    file_path = fn
    self.P("Loading '{}'...".format(file_path))
    if ext.lower() == '.zip':
      df = pd.read_pickle(file_path)
    else:
      if timestamps is not None:
        if type(timestamps) is str:
          timestamps = [timestamps]
        df = pd.read_csv(file_path, parse_dates=timestamps)
      else:
        df = pd.read_csv(file_path)
    return df

  def save_dataframe(self,
                     df, fn='', show_prefix=False,
                     folder='data',
                     ignore_index=True, compress=False,
                     mode='w', header=True,
                     also_markdown=False,
                     to_data=None,
                     full_path=None,
                     subfolder_path=None
                     ):
    """
     df: dataframe
     fn: name of file
     folder: None - absolute path, 'data' - save to data ... etc
     show_prefix: add timestamp prefix
     (obsolete) to_data: False to save in output dir instead of data dir
     compress: save to zipped pickle
     (obsolete) full_path : if full path is specified then file is saved to fn ignoring anything else
     mode: the writing mode in csv (default 'w' - write). Could be also 'a' - append
     header: bool or list of str, default True
        Write out the column names. If a list of strings is given it is assumed to be aliases for the column names.
        This may be set to False for 'append' mode, for all but not the first save call.

     subfolder_path : str, optional
      A path relative to '_data' or `folder` value (if `to_data=False`) where the dataframe is saved
      Default is None.
    """
    if to_data is not None:
      self.P("WARNING: `to_data` is obsolete, please use `folder='data'`")
    if full_path is not None:
      self.P("WARNING: `full_path` is obsolete, please use `folder=None`")

    if compress:
      ext = '.zip'
    else:
      ext = '.csv'

    if fn[-4:] != ext:
      fn += ext

    assert folder in [None, 'data', 'output', 'models']
    lfld = self.get_target_folder(target=folder)
    if to_data:
      lfld = self._data_dir

    if subfolder_path is not None:
      lfld = os.path.join(lfld, subfolder_path.lstrip('/'))

    if lfld is not None:
      file_prefix = '' if not show_prefix else self.file_prefix + "_"
      save_path = lfld
      file_name = file_prefix + fn
      out_file = os.path.join(save_path, file_name)
    else:
      out_file = fn
      save_path, file_name = os.path.split(out_file)

    self.P("Saving (mode='{}') {:<20} [{}] ..{}".format(
      mode, file_name, df.shape, save_path[-30:]))
    if compress:
      df.to_pickle(out_file)
    else:
      df.to_csv(out_file, index=not ignore_index, mode=mode, header=header)

    if also_markdown:
      has_tabulate = True
      try:
        import imp
        imp.find_module('tabulate')
      except:
        has_tabulate = False
      if not has_tabulate:
        self.raise_error(
          "In order to generate markdown (`also_markdown=True`) you need to install (pip or conda) tabulate")
      fn_md = os.path.join(save_path, file_name + '.md')
      with open(fn_md, 'wt') as fmd:
        fmd.write(df.to_markdown())

    return file_name, out_file

  def save_dataframe_current_time(self,
                                  df, fn=''):
    """
    saves a DataFrame in 'output' folder with current time prefix
    """
    file_prefix = dt.now().strftime("%Y%m%d_%H%M%S")
    csvfile = os.path.join(self._outp_dir, file_prefix + fn + '.csv')
    df.to_csv(csvfile)
    return csvfile

  @staticmethod
  def get_dataframe_info(df):
    # setup the environment
    old_stdout = sys.stdout
    sys.stdout = TextIOWrapper(BytesIO(), sys.stdout.encoding)
    # write to stdout or stdout.buffer
    df.info()
    # get output
    sys.stdout.seek(0)  # jump to the start
    out = sys.stdout.read()  # read output
    # restore stdout
    sys.stdout.close()
    sys.stdout = old_stdout

    str_result = "DataFrame info:\n" + out
    return str_result

  def save_dataframe_to_hdf(self,
                            df, h5_file, h5_format='table'):
    """
     saves pandas df to h5_file in _data folder
     assume h5_file DOES NOT HAVE path info
    """
    assert "/" not in h5_file
    assert "\\" not in h5_file
    table_name, ext = os.path.splitext(h5_file)
    out_file = os.path.join(self._data_dir, h5_file)
    self.verbose_log("Saving ...{}".format(out_file[-40:]))
    df.to_hdf(out_file, key='table_' + table_name,
              append=False, format=h5_format)
    self.verbose_log("Done saving ...{}".format(out_file[-40:]), show_time=True)
    return

  def load_dataframe_from_hdf(self,
                              h5_file):
    """
     loads pandas dataframe from h5 file store
     assume h5_file DOES NOT HAVE path info
    """
    import pandas as pd

    assert "/" not in h5_file
    assert "\\" not in h5_file
    table_name, ext = os.path.splitext(h5_file)
    out_file = os.path.join(self._data_dir, h5_file)
    self.verbose_log("Loading ...{}".format(out_file[-40:]))
    df = pd.read_hdf(out_file, key='table_' + table_name)
    self.verbose_log("Done loading ...{}".format(out_file[-40:]), show_time=True)
    return df

  @staticmethod
  def drop_constant_columns(df):
    """
    Drops constant value columns of pandas dataframe.
    """
    return df.loc[:, (df != df.iloc[0]).any()]

  @staticmethod
  def remove_constant_columns(df):
    """
    removes constant dataframe columns
    """
    if df.shape[0] <= 1:
      return df
    good_columns = []
    for col in df.columns:
      if df[col].astype(str).nunique() > 1:
        good_columns.append(col)
    return df[good_columns]
