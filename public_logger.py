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

from libraries.base_logger import BaseLogger
from libraries.logger_mixins import (
  _TimersMixin,
  _MatplotlibMixin,
  _HistogramMixin,
  _DateTimeMixin,
  _DataFrameMixin,
  _GeneralSerializationMixin,
  _JSONSerializationMixin,
  _PickleSerializationMixin,
  _DownloadMixin,
  _UploadMixin,
  _ProcessMixin,
  _MachineMixin,
  _GPUMixin,
  _PackageLoaderMixin,
  _PublicTFKerasMixin,
  _UtilsMixin
)

class DotDict(dict):
  __getattr__ = dict.__getitem__
  __setattr__ = dict.__setitem__
  __delattr__ = dict.__delitem__

class Logger(
  BaseLogger,
  _DataFrameMixin,
  _DateTimeMixin,
  _DownloadMixin,
  _GPUMixin,
  _HistogramMixin,
  _MachineMixin,
  _MatplotlibMixin,
  _PackageLoaderMixin,
  _ProcessMixin,
  _PublicTFKerasMixin,
  _GeneralSerializationMixin,
  _JSONSerializationMixin,
  _PickleSerializationMixin,
  _TimersMixin,
  _UploadMixin,
  _UtilsMixin
):

  def __init__(self, lib_name="",
               lib_ver="",
               config_file="",
               base_folder=None,
               app_folder=None,
               show_time=True,
               config_file_encoding=None,
               no_folders_no_save=False,
               max_lines=None,
               HTML=False,
               DEBUG=True,
               data_folder_additional_configs=None,
               TF_KERAS=True):

    super(Logger, self).__init__(
      lib_name=lib_name, lib_ver=lib_ver,
      config_file=config_file,
      base_folder=base_folder,
      app_folder=app_folder,
      show_time=show_time,
      config_file_encoding=config_file_encoding,
      no_folders_no_save=no_folders_no_save,
      max_lines=max_lines,
      HTML=HTML,
      DEBUG=DEBUG,
      data_folder_additional_configs=data_folder_additional_configs
    )

    self.reset_timers()

    self.verbose_log('  Avail/Total RAM: {:.1f} GB / {:.1f} GB'.format(
      self.get_avail_memory(), self.get_machine_memory()
    ), color='green')

    if TF_KERAS:
      self.check_tf()
    return

