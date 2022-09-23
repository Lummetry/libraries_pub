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
import json
import shutil
import codecs
import textwrap
import numpy as np
import traceback
import socket
import threading

from time import time as tm
from collections import OrderedDict
from datetime import datetime as dt
from datetime import timedelta
from pathlib import Path

__VER__ = '9.5.0'

_HTML_START = "<HEAD><meta http-equiv='refresh' content='5' ></HEAD><BODY><pre>"
_HTML_END = "</pre></BODY>"

COLORS = {
  'r': "\x1b[1;31m",
  'g': "\x1b[1;32m",
  'y': "\x1b[1;33m",
  'b': "\x1b[1;34m",
  'm': "\x1b[1;35m",
  'a': "\x1b[41m",
  'e': "\x1b[41m",
  'w': "\x1b[1;31m",

  '__end__': "\x1b[0m",
}

_LOGGER_LOCK_ID = '_logger_print_lock' 

class BaseLogger(object):

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
               data_folder_additional_configs=None
               ):

    super(BaseLogger, self).__init__()
    if os.name == 'nt':
      os.system('color')
    self.__lib__ = lib_name
    self.show_time = show_time
    self.no_folders_no_save = no_folders_no_save
    self.max_lines = max_lines
    self.HTML = HTML
    self.DEBUG = DEBUG
    self.log_suffix = lib_name
    
    self._lock_table = OrderedDict({
      _LOGGER_LOCK_ID: threading.Lock(),
      })

    self._base_folder = base_folder
    self._app_folder = app_folder
    self._normalize_path_sep()

    self.data_folder_additional_configs = data_folder_additional_configs

    self.__version__ = __VER__
    self.version = self.__version__
    self.file_prefix = None
    self.refresh_file_prefix()

    self.last_time = tm()
    self.app_log = list()
    self.split_part = 1
    self.config_data = None
    self.MACHINE_NAME = None
    self.COMPUTER_NAME = None
    self.processor_platform = None
    self.python_version = sys.version.split(' ')[0]
    self.python_major = int(self.python_version.split('.')[0])
    self.python_minor = int(self.python_version.split('.')[1])
    if self.python_major < 3:
      self.P("WARNING: Python 2 or lower detected. Run will fail!", color='error')
      
    _ = self.get_machine_name()
    
    self.analyze_processor_platform()

    self._configure_data_and_dirs(config_file, config_file_encoding)
    self._generate_log_path()
    self._check_additional_configs()
    
    self.git_branch = self.get_active_git_branch()
    self.conda_env = self.get_conda_env()

    if lib_ver == "":
      lib_ver = __VER__
    ver = "v{}".format(lib_ver) if lib_ver != "" else ""
    self.verbose_log(
      "Library [{} {}] initialized on machine [{}][{}].".format(
        self.__lib__, ver, self.MACHINE_NAME, self.get_processor_platform(),
      ),
      color='green'
    )
    self.verbose_log("  Logger v{}.".format(self.__version__),color='green')


    if self.DEBUG:
      self.P('  DEBUG is enabled in Logger', color='g')
    else:
      self.P('  WARNING: Debug is NOT enabled in Logger, some functionalities are DISABLED', color='r')

    return
  
  def is_running(self, verbose=True):
    return self.same_script_already_running(verbose=verbose)
    
  
  def same_script_already_running(self, verbose=True):
    import psutil
    CMD = 'python'
    script_file = sys.argv[0]
    if script_file == '':
      self.P("Cannot get script file name", color='r')
      return False
    for q in psutil.process_iter():
      if q.name().startswith(CMD):
        if (
            len(q.cmdline())>1 and 
            script_file in q.cmdline()[1] and 
            q.pid != os.getpid()
            ):
          if verbose:
            self.P("Python '{}' process is already running".format(script_file), color='m')
          return True
    return False
  
  def lock_process(self, str_lock_name):
    if os.name == 'nt':
      # windows
      from win32event import CreateMutex
      from win32api import GetLastError
      from winerror import ERROR_ALREADY_EXISTS
      str_lock_name = "Global\\" + str_lock_name.replace("\\","")
      self.P("Attempting to create lock on current Windows process for id '{}'".format(str_lock_name), color='m')
      
      try:
        mutex_handle = CreateMutex(None, 1, str_lock_name)
        err = GetLastError()
      except:
        self.P("Exception in process locking id '{}'".format(str_lock_name), color='r')
        err = ERROR_ALREADY_EXISTS
        
      if err == ERROR_ALREADY_EXISTS:
        # maybe show some text
        self.P("Another Windows process has already acquired id '{}'".format(str_lock_name), color='r')
        return None
      else:
        # maybe show some text
        self.P("Current Windows process has acquired id '{}':{} ({})".format(
          str_lock_name, mutex_handle, err), color='g')
        return mutex_handle    
    else:
      import platform
      str_platform = platform.system()
      if str_platform.lower() == 'darwin':
        # macos
        self.P("Running on MacOS. Skipping mutex and checking if script is running", color='m')
        if self.same_script_already_running():
          return None        
        return -1
      else:         
        import socket
        self.P("Attempting to create lock on current Linux process for id '{}'".format(str_lock_name), color='m')
        _lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        try:
          _lock_socket.bind('\0' + str_lock_name)
          # maybe show some text
          self.P("Current Linux process has acquired id '{}': {}".format(
            str_lock_name, _lock_socket), color='g')
          return _lock_socket
        except Exception as err:
          # maybe show some text
          self.P("Another Linux process has already acquired id '{}'. Error: {}".format(
            str_lock_name, err), color='r')
          return None
      # end if platform
    # end if not windows
    return
  
  def analyze_processor_platform(self):
    import platform
    import subprocess
    import re
    str_system = platform.system()
    if str_system == "Windows":
      self.processor_platform = platform.processor()
    elif str_system == "Darwin":
      os.environ['PATH'] = os.environ['PATH'] + os.pathsep + '/usr/sbin'
      command ="sysctl -n machdep.cpu.brand_string"
      self.processor_platform = subprocess.check_output(command, shell=True).strip().decode('utf-8')
    elif str_system == "Linux":
      command = "cat /proc/cpuinfo"
      all_info = subprocess.check_output(command, shell=True).decode().strip()
      for line in all_info.split("\n"):
        if "model name" in line:
          self.processor_platform = re.sub( ".*model name.*:", "", line,1)    
          break
    return
  
  def get_processor_platform(self):
    return self.processor_platform
    
  
  def lock_resource(self, str_res):
    if str_res not in self._lock_table:
      self._lock_table[str_res] = threading.Lock()
    self._lock_table[str_res].acquire(blocking=True)
    return
  
  def unlock_resource(self, str_res):
    if str_res in self._lock_table:
      self._lock_table[str_res].release()
    return
  
  def lock_logger(self):
    self.lock_resource(_LOGGER_LOCK_ID)
    return
  
  def unlock_logger(self):
    self.unlock_resource(_LOGGER_LOCK_ID)
    
  def get_file_path(self, fn, folder, subfolder_path=None, force=False):
    lfld = self.get_target_folder(target=folder)
    if lfld is None:
      datafile = fn
    else:
      datafolder = lfld
    if subfolder_path is not None:
      datafolder = os.path.join(datafolder, subfolder_path.lstrip('/'))
    datafile = os.path.join(datafolder, fn)
    if os.path.isfile(datafile) or force:
      return datafile
    return 
    

  @property
  def session_id(self):
    return self.file_prefix
  
  
  def cleanup_logs(self, days=10):
    self.P("Cleanup logs...", color='y')
    str_old_date = (dt.today() - timedelta(days=days)).strftime('%Y%m%d')
    int_old_date = int(str_old_date)
    logs = os.listdir(self._logs_dir)
    for fn in logs:
      if fn[-4:] == '.txt':
        str_date = fn[:8]
        int_date = None
        if len(str_date) > 8:
          try:
            int_date = int(str_date)
          except:
            pass
        if int_date is not None and int_date <= int_old_date:
          self.P("  Deleting old log file '{}'".format(fn), color='y')
          full_fn = os.path.join(self._logs_dir, fn)
          os.remove(full_fn)
    return
                    


  def _logger(self, logstr, show=True, noprefix=False, show_time=False, color=None):
    """
    log processing method
    """
    self.lock_logger()
    # now that we have locking in place we no longer need to cancel in-thread logging    
    # if not self.is_main_thread:
    #   return
    self.start_timer('_logger', section='LOGGER_internal')

    elapsed = tm() - self.last_time

    self.start_timer('_logger_add_log', section='LOGGER_internal')
    self._add_log(
      logstr, show=show,
      noprefix=noprefix,
      show_time=show_time,
      color=color
    )
    self.end_timer('_logger_add_log', section='LOGGER_internal')

    self.start_timer('_logger_save_log', section='LOGGER_internal')
    self._save_log()
    self.end_timer('_logger_save_log', section='LOGGER_internal')
    
    self.last_time = tm()
    self._check_log_size()

    self.end_timer('_logger', section='LOGGER_internal')    
    self.unlock_logger()
    return elapsed

  def _normalize_path_sep(self):
    if self._base_folder is not None:
      if os.path.sep == '\\':
        self._base_folder = self._base_folder.replace('/', '\\')
      else:
        self._base_folder = self._base_folder.replace('\\', '/')
      #endif
    #endif

    if self._app_folder is not None:
      if os.path.sep == '\\':
        self._app_folder = self._app_folder.replace('/', '\\')
      else:
        self._app_folder = self._app_folder.replace('\\', '/')
      #endif
    #endif

    return

  def print_on_columns(self, *objects, nr_print_columns=4, nr_print_chars=12, header=None, color=None):
    if header:
      self.P(header, color=color)

    print_columns = [[] for _ in range(nr_print_columns)]

    crt_column = 0
    _fmt = "{:>" + str(nr_print_chars) + "}"

    nr_labels_per_column = int(np.ceil(len(objects) / nr_print_columns))
    for i, obj in enumerate(objects):
      if i // nr_labels_per_column != crt_column:
        crt_column += 1

      print_columns[crt_column].append(_fmt.format(obj[:nr_print_chars]))
    # endfor

    for i in range(nr_labels_per_column):
      str_line = ''
      for j in range(nr_print_columns):
        if i >= len(print_columns[j]):
          continue

        str_line += print_columns[j][i] + '    '

      self.P(str_line, noprefix=True, color=color)
    # endfor
    return

  def _add_log(self, logstr, show=True, noprefix=False, show_time=False, color=None):
    if type(logstr) != str:
      logstr = str(logstr)
    if logstr == "":
      logstr = " "
    if 'WARNING' in logstr and color is None:
      color = 'warning'
    if 'ERROR' in logstr and color is None:
      color = 'error'
    elapsed = tm() - self.last_time
    nowtime = dt.now()
    prefix = ""
    strnowtime = nowtime.strftime("[{}][%Y-%m-%d %H:%M:%S] ".format(self.__lib__))
    if self.show_time and (not noprefix):
      prefix = strnowtime
    if logstr[0] == "\n":
      logstr = logstr[1:]
      prefix = "\n" + prefix
    res_log = logstr
    logstr = prefix + logstr
    if show_time:
      logstr += " [{:.2f}s]".format(elapsed)
    self.app_log.append(logstr)
    if show:
      if color is not None:
        clr = COLORS.get(color[0], None)
        _color_start = clr
        _color_end = COLORS['__end__']
        if clr is None:
          print("ERROR: unknown color '{}' - available colors are: {}".format(
            color, ', '.join([v + k + _color_end for k, v in COLORS.items()])
          ))
        else:
          logstr = _color_start + logstr + _color_end

      print("\r" + logstr, flush=True)
    #endif
    return

  def _save_log(self, DEBUG_ERRORS=False):
    if self.no_folders_no_save:
      return
    nowtime = dt.now()
    strnowtime = nowtime.strftime("[{}][%Y-%m-%d %H:%M:%S] ".format(self.__lib__))
    stage = 0
    try:
      log_output = codecs.open(self.log_file, "w", "utf-8")  # open(self.log_file, 'w+')
      stage += 1
      if self.HTML:
        log_output.write(_HTML_START)
        stage += 1
        iter_list = reversed(self.app_log)
      else:
        iter_list = self.app_log
      for log_item in iter_list:
        # if self.HTML:
        #  log_output.write("%s<BR>\n" % log_item)
        # else:
        log_output.write("{}\n".format(log_item))
        stage += 1
      if self.HTML:
        log_output.write(_HTML_END)
        stage += 1
      log_output.close()
      stage += 1
    except:
      if DEBUG_ERRORS:
        print(strnowtime + "LogWErr S: {} [{}]".format(stage,
                                                       sys.exc_info()[0]), flush=True)
    return

  def _check_log_size(self):
    if self.max_lines is None:
      return

    if len(self.app_log) >= self.max_lines:
      self._add_log("Ending log part {}".format(self.split_part))
      self._save_log()
      self.app_log = []
      self.split_part += 1
      self._generate_log_path()
      self._add_log("Starting log part {}".format(self.split_part))
      self._save_log()
    return

  def verbose_log(self, str_msg, show_time=False, noprefix=False, color=None):
    return self._logger(
      str_msg,
      show=True,
      show_time=show_time,
      noprefix=noprefix, color=color
    )

  def P(self, str_msg, show_time=False, noprefix=False, color=None):
    return self.p(str_msg, show_time=show_time, noprefix=noprefix, color=color)

  @staticmethod
  def Pr(str_msg, show_time=False, noprefix=False):
    if type(str_msg) != str:
      str_msg = str(str_msg)
    print("\r" + str_msg, flush=True, end='')

  def p(self, str_msg, show_time=False, noprefix=False, color=None):
    return self._logger(
      str_msg,
      show=True,
      show_time=show_time,
      noprefix=noprefix, color=color
    )

  def Pmd(self, s=''):
    print_func = None
    try:
      from IPython.display import Markdown, display
      def print_func(s):
        display(Markdown(s))
    except:
      pass
    if type(s) != str:
      s = str(s)

    if print_func is not None:
      self._add_log(
        logstr=s,
        show=False,
        noprefix=False,
        show_time=False,
      )
      print_func(s)
    else:
      self.P(s)
    return

  def Pmdc(self, s=''):
    print_func = None
    try:
      from IPython.display import Markdown, display
      def print_func(s):
        display(Markdown(s))
    except:
      pass
    if type(s) != str:
      s = str(s)

    if print_func is not None:
      self._add_log(
        logstr=s,
        show=False,
        noprefix=False,
        show_time=False,
      )
      print_func('<strong>' + s + '</strong>')
    else:
      self.P(s)
    return

  def print_pad(self, str_msg, str_text, n=3):
    if type(str_msg) != str:
      str_msg = str(str_msg)
    if type(str_text) != str:
      str_text = str(str_text)
    str_final = str_msg + "\n" + textwrap.indent(str_text, n * " ")
    self._logger(str_final, show=True, show_time=False)
    return

  def log(self, str_msg, show=False, show_time=False, color=None):
    return self._logger(str_msg, show=show, show_time=show_time, color=color)

  def _generate_log_path(self):
    if self.no_folders_no_save:
      return
    part = '{:03d}'.format(self.split_part)
    lp = self.file_prefix
    ls = self.log_suffix
    if self.HTML:
      self.log_file = lp + '_' + ls + '_' + part + '_log_web.html'
    else:
      self.log_file = lp + '_' + ls + '_' + part + '_log.txt'

    self.log_file = os.path.join(self._logs_dir, self.log_file)
    path_dict = {}
    path_dict['CURRENT_LOG'] = self.log_file
    file_path = os.path.join(self._logs_dir, self.__lib__ + '.txt')
    with open(file_path, 'w') as fp:
      json.dump(path_dict, fp, sort_keys=True, indent=4)
    self._add_log("{} log changed to {}...".format(file_path, self.log_file))
    return

  def _get_cloud_base_folder(self, base_folder):
    upper = base_folder.upper()
    google = "GOOGLE" in upper
    dropbox = "DROPBOX" in upper

    if google and not "/DATA/" in upper:
      base_folder = self.get_google_drive()
    if dropbox and not "/DATA/" in upper:
      base_folder = self.get_dropbox_drive()
    return base_folder

  def _configure_data_and_dirs(self, config_file, config_file_encoding=None):
    if self.no_folders_no_save:
      return

    if config_file != "":
      if config_file_encoding is None:
        f = open(config_file)
      else:
        f = open(config_file, encoding=config_file_encoding)

      self.config_data = json.load(f, object_pairs_hook=OrderedDict)

      if self._base_folder is None and self._app_folder is None:
        assert ("BASE_FOLDER" in self.config_data.keys())
        assert ("APP_FOLDER" in self.config_data.keys())
        self._base_folder = self.config_data["BASE_FOLDER"]
        self._app_folder = self.config_data["APP_FOLDER"]
      #endif

      print("Loaded config [{}]".format(config_file), flush=True)
      self.config_file = config_file
    else:
      self.config_data = {
        'BASE_FOLDER' : self._base_folder,
        'APP_FOLDER' : self._app_folder
      }
      self.config_file = "default_config.txt"
    #endif

    self._base_folder = self.expand_tilda(self._base_folder)
    self._base_folder = self._get_cloud_base_folder(self._base_folder)
    self._root_folder = self._base_folder
    self._base_folder = os.path.join(self._base_folder, self._app_folder)
    print("BASE: {}".format(self._base_folder), flush=True)

    self._normalize_path_sep()

    if not os.path.isdir(self._base_folder):
      print("{color_start}WARNING! Invalid app base folder '{base_folder}'! We create it automatically!{color_end}".format(
        color_start=COLORS['r'],
        base_folder=self._base_folder,
        color_end=COLORS['__end__']
      ), flush=True)
    #endif

    self._logs_dir = os.path.join(self._base_folder, self.get_logs_dir_name())
    self._outp_dir = os.path.join(self._base_folder, self.get_output_dir_name())
    self._data_dir = os.path.join(self._base_folder, self.get_data_dir_name())
    self._modl_dir = os.path.join(self._base_folder, self.get_models_dir_name())

    self._setup_folders([
      self._outp_dir,
      self._logs_dir,
      self._data_dir,
      self._modl_dir
    ])

    return

  @staticmethod
  def get_logs_dir_name():
    return '_logs'

  @staticmethod
  def get_output_dir_name():
    return '_output'

  @staticmethod
  def get_data_dir_name():
    return '_data'

  @staticmethod
  def get_models_dir_name():
    return '_models'

  def _setup_folders(self, folder_list):
    self.folder_list = folder_list
    for folder in folder_list:
      if not os.path.isdir(folder):
        print("Creating folder [{}]".format(folder))
        os.makedirs(folder)
    return

  def update_config(self, dict_newdata=None):
    """
     saves config file with current config_data dictionary
    """
    if dict_newdata is not None:
      for key in dict_newdata:
        self.config_data[key] = dict_newdata[key]
    with open(self.config_file, 'w') as fp:
      json.dump(self.config_data, fp, sort_keys=True, indent=4)
    self.P("Config file '{}' has been updated.".format(self.config_file))
    return

  def _check_additional_configs(self):
    additional_configs = []

    check_dir = self.get_data_folder()
    if self.data_folder_additional_configs is not None:
      check_dir = self.get_data_subfolder(self.data_folder_additional_configs)
      if check_dir is None:
        self.P("Additional configs folder '{}' not found in '{}'"
               .format(self.data_folder_additional_configs, self.get_data_folder()[-50:]))
        return

    data_files = list(filter(lambda x: os.path.isfile(os.path.join(check_dir, x)), os.listdir(check_dir)))
    data_files = list(filter(lambda x: any(ext in x for ext in ['.txt', 'json']), data_files))

    for f in data_files:
      if any(x in f for x in ['config', 'cfg', 'conf']):
        fn = self.get_data_file(f)
        self.P("Found additional config in '{}'".format(fn))
        additional_configs.append(json.load(open(fn), object_pairs_hook=OrderedDict))

    if len(additional_configs) > 0:
      dct_final = {}
      for d in additional_configs:
        dct_final.update(d)
      for k, v in dct_final.items():
        if k in self.config_data:
          self.P("[WARNING] Overriding key '{}'".format(k))
        self.config_data[k] = v
    return

  def raise_error(self, error_message):
    self.P("ERROR: {}".format(error_message))
    raise ValueError(str(error_message))

  def get_config_value(self, key, default=0):
    if key in self.config_data.keys():
      _val = self.config_data[key]
    else:
      # create key if does not exist
      _val = default
      self.config_data[key] = _val
    return _val

  def clear_folder(self, folder, include_subfolders=False):
    self.P("Clearing {}".format(folder))
    for the_file in os.listdir(folder):
      file_path = os.path.join(folder, the_file)
      try:
        if os.path.isfile(file_path):
          self.P("  Deleting {}".format(file_path[-30:]))
          os.unlink(file_path)
        elif os.path.isdir(file_path) and include_subfolders:
          self.P("  Removing ...{} subfolder".format(file_path[-30:]))
          shutil.rmtree(file_path)
      except Exception as e:
        self.P("{}".format(e))

  def clear_model_folder(self, include_subfolders=False):
    folder = self.get_models_folder()
    self.clear_folder(folder, include_subfolders=include_subfolders)

  def clear_log_folder(self, include_subfolders=False):
    folder = self._logs_dir
    self.clear_folder(folder, include_subfolders=include_subfolders)

  def clear_output_folder(self, include_subfolders=False):
    folder = self.get_output_folder()
    self.clear_folder(folder, include_subfolders=include_subfolders)

  def clear_all_results(self):
    self.P("WARNING: removing all files from models, logs and output!")
    self.clear_log_folder()
    self.clear_model_folder()
    self.clear_output_folder()

  def get_base_folder(self):
    return self._base_folder if hasattr(self, '_base_folder') else ''

  @property
  def base_folder(self):
    return self.get_base_folder()

  @property
  def root_folder(self):
    return self._root_folder

  @property
  def app_folder(self):
    return self._app_folder

  def get_data_folder(self):
    return self._data_dir if hasattr(self, '_data_dir') else ''

  def get_logs_folder(self):
    return self._logs_dir if hasattr(self, '_logs_dir') else ''

  def get_output_folder(self):
    return self._outp_dir if hasattr(self, '_outp_dir') else ''

  def get_models_folder(self):
    return self._modl_dir if hasattr(self, '_modl_dir') else ''

  def get_target_folder(self, target):
    if target is None:
      return

    if target.lower() in ['data', '_data', 'data_dir', 'dat']:
      return self.get_data_folder()

    if target.lower() in ['logs', 'log', 'logs_dir', 'log_dir', '_log', '_logs']:
      return self.get_logs_folder()

    if target.lower() in ['models', 'model', '_models', '_model', 'model_dir', 'models_dir', 'modl']:
      return self.get_models_folder()

    if target.lower() in ['output', '_output', 'output_dir', 'outp', '_outp']:
      return self.get_output_folder()

    self.P("Inner folder for target '{}' not found".format(target))
    return

  def get_data_subfolder(self, _dir):
    _data = self.get_data_folder()
    _path = os.path.join(_data, _dir)
    if os.path.isdir(_path):
      return _path
    return None

  def get_models_subfolder(self, _dir):
    _data = self.get_models_folder()
    _path = os.path.join(_data, _dir)
    if os.path.isdir(_path):
      return _path
    return None
  
  def get_output_subfolder(self, _dir):
    _data = self.get_output_folder()
    _path = os.path.join(_data, _dir)
    if os.path.isdir(_path):
      return _path
    return None

  def get_path_from_node(self, dct):
    if 'PARENT' in dct:
      path = self.get_path_from_node(dct['PARENT'])
      os.path.join(path, dct['PATH'])
      return path
    elif 'USE_DROPBOX' in dct and int(dct['USE_DROPBOX']) == 1:
      return os.path.join(self.get_base_folder(), dct['PATH'])
    else:
      return dct['PATH']

  def get_root_subfolder(self, folder):
    fld = os.path.join(self._root_folder, folder)
    if os.path.isdir(fld):
      return fld
    else:
      return None

  def get_base_subfolder(self, folder):
    fld = os.path.join(self._base_folder, folder)
    if os.path.isdir(fld):
      return fld
    else:
      return None

  def get_root_file(self, str_file):
    fn = os.path.join(self._root_folder, str_file)
    assert os.path.isfile(fn), "File not found: {}".format(fn)
    return fn

  def get_base_file(self, str_file):
    fn = os.path.join(self.get_base_folder(), str_file)
    assert os.path.isfile(fn), "File not found: {}".format(fn)
    return fn

  def get_file_from_folder(self, s_folder, s_file):
    s_fn = os.path.join(self.get_base_folder(), s_folder, s_file)
    if not os.path.isfile(s_fn):
      s_fn = None
    return s_fn

  def get_data_file(self, s_file):
    """
    returns full path of a data file or none is file does not exist
    """
    fpath = os.path.join(self.get_data_folder(), s_file)
    if not os.path.isfile(fpath):
      fpath = None
    return fpath

  def get_model_file(self, s_file):
    """
    returns full path of a data file or none is file does not exist
    """
    fpath = os.path.join(self.get_models_folder(), s_file)
    if not os.path.isfile(fpath):
      fpath = None
    return fpath

  def get_models_file(self, s_file):
    return self.get_model_file(s_file)

  def get_output_file(self, s_file):
    fpath = os.path.join(self.get_output_folder(), s_file)
    if not os.path.isfile(fpath):
      fpath = None
    return fpath

  def check_folder(self, sub_folder, root=None):
    if root is None:
      root = self.get_base_folder()
    sfolder = os.path.join(root, sub_folder)
    if sfolder not in self.folder_list:
      self.folder_list.append(sfolder)

    if not os.path.isdir(sfolder):
      self.verbose_log(" Creating folder [...{}]".format(sfolder[-40:]))
      os.makedirs(sfolder)
    return sfolder

  def check_folder_data(self, sub_folder):
    root = self.get_data_folder()
    return self.check_folder(sub_folder, root)

  def check_folder_models(self, sub_folder):
    root = self.get_models_folder()
    return self.check_folder(sub_folder, root)

  def check_folder_output(self, sub_folder):
    root = self.get_output_folder()
    return self.check_folder(sub_folder, root)

  @staticmethod
  def get_folders(path):
    lst = [os.path.join(path, x) for x in os.listdir(path)]
    return [x for x in lst if os.path.isdir(x)]

  @staticmethod
  def expand_tilda(path):
    if '~' in path:
      path = path.replace('~', os.path.expanduser('~'))
    return path

  def refresh_file_prefix(self):
    self.file_prefix = dt.now().strftime("%Y%m%d_%H%M%S")
    return

  @staticmethod
  def now_str(nice_print=False, short=False):
    if nice_print:
      if short:        
        return dt.now().strftime("%Y-%m-%d %H:%M:%S")
      else:
        return dt.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    else:
      if short:
        return dt.now().strftime("%Y%m%d%H%M%S") 
      else:
        return dt.now().strftime("%Y%m%d%H%M%S%f")

  @staticmethod
  def now_str_fmt(fmt=None):
    if fmt is None:
      fmt = '%Y-%m-%d %H:%M:%S.%f'

    return dt.now().strftime(fmt)

  def get_error_info(self, return_err_val=False):
    """
    Returns error_type, file, method, line for last error if available

    Parameters
    ----------
    return_err_val: boolean, optional
      Whether the method returns or not the error message (err_val)

    Returns
    -------
    if not return_err_val:
      (tuple) str, str, str, str : errortype, file, method, line
    else:
      (tuple) str, str, str, str, str : errortype, file, method, line, err message
    """
    err_type, err_val, err_trace = sys.exc_info()
    if False:
      # dont try this at home :) if you want to pickle a logger instance after
      # `get_error_info` was triggered, then it won't work because `self._last_extracted_error`
      # contain an object of type `traceback` and tracebacks cannot be pickled
      self._last_extracted_error = err_type, err_val, err_trace
    # endif
    if err_type is not None:
      str_err = err_type.__name__
      stack_summary = traceback.extract_tb(err_trace)
      last_error_frame = stack_summary[-1]
      fn = os.path.splitext(os.path.split(last_error_frame.filename)[-1])[0]
      lineno = last_error_frame.lineno
      func_name = last_error_frame.name
      if not return_err_val:
        return str_err, fn, func_name, lineno
      else:
        return str_err, fn, func_name, lineno, str(err_val)
    else:
      return "", "", "", "", ""

  @staticmethod
  def tqdm_enumerate(_iter):
    from tqdm import tqdm
    i = 0
    for y in tqdm(_iter):
      yield i, y
      i += 1

  @staticmethod
  def set_nice_prints(linewidth=500,
                      precision=2,
                      np_precision=None,
                      df_precision=None,
                      suppress=False):

    if np_precision is None:
      np_precision = precision
    if df_precision is None:
      df_precision = precision
    np.set_printoptions(precision=np_precision)
    np.set_printoptions(floatmode='fixed')
    np.set_printoptions(linewidth=linewidth)
    np.set_printoptions(suppress=suppress)

    try:
      import pandas as pd
      pd.set_option('display.max_rows', 500)
      pd.set_option('display.max_columns', 500)
      pd.set_option('display.width', 1000)
      pd.set_option('display.max_colwidth', 1000)
      _format = '{:.' + str(df_precision) + 'f}'
      pd.set_option('display.float_format', lambda x: _format.format(x))
    except:
      pass

    return

  @staticmethod
  def get_google_drive():
    home_dir = os.path.expanduser("~")
    valid_paths = [
      os.path.join(home_dir, "Google Drive"),
      os.path.join(home_dir, "GoogleDrive"),
      os.path.join(os.path.join(home_dir, "Desktop"), "Google Drive"),
      os.path.join(os.path.join(home_dir, "Desktop"), "GoogleDrive"),
      os.path.join("C:/", "GoogleDrive"),
      os.path.join("C:/", "Google Drive"),
      os.path.join("D:/", "GoogleDrive"),
      os.path.join("D:/", "Google Drive"),
    ]

    drive_path = None
    for path in valid_paths:
      if os.path.isdir(path):
        drive_path = path
        break

    if drive_path is None:
      raise Exception("Couldn't find google drive folder!")

    return drive_path

  @staticmethod
  def get_dropbox_drive():
    home_dir = os.path.expanduser("~")
    valid_paths = [
      os.path.join(home_dir, "Lummetry.AI Dropbox/DATA"),
      os.path.join(home_dir, "Lummetry.AIDropbox/DATA"),
      os.path.join(os.path.join(home_dir, "Desktop"), "Lummetry.AI Dropbox/DATA"),
      os.path.join(os.path.join(home_dir, "Desktop"), "Lummetry.AIDropbox/DATA"),
      os.path.join("C:/", "Lummetry.AI Dropbox/DATA"),
      os.path.join("C:/", "Lummetry.AIDropbox/DATA"),
      os.path.join("D:/", "Lummetry.AI Dropbox/DATA"),
      os.path.join("D:/", "Lummetry.AIDropbox/DATA"),
      os.path.join(home_dir, "Dropbox/DATA"),
      os.path.join(os.path.join(home_dir, "Desktop"), "Dropbox/DATA"),
      os.path.join("C:/", "Dropbox/DATA"),
      os.path.join("D:/", "Dropbox/DATA"),
    ]

    drive_path = None
    for path in valid_paths:
      if os.path.isdir(path):
        drive_path = path
        break

    if drive_path is None:
      raise Exception("Couldn't find google drive folder!")

    return drive_path

  @staticmethod
  def get_dropbox_subfolder(sub_folder):
    drop_root = BaseLogger.get_dropbox_drive()
    full = os.path.join(drop_root, sub_folder)
    if os.path.isdir(full):
      return full
    else:
      return None

  @staticmethod
  def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    Credits: django 3.1
    """
    from importlib import import_module
    try:
      module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError as err:
      raise ImportError("%s doesn't look like a module path" % dotted_path) from err

    module = import_module(module_path)

    try:
      return getattr(module, class_name)
    except AttributeError as err:
      raise ImportError(
        'Module "%s" does not define a "%s" attribute/class' % \
        (module_path, class_name)
      ) from err

  def get_machine_name(self):
    """
    if socket.gethostname().find('.')>=0:
        name=socket.gethostname()
    else:
        name=socket.gethostbyaddr(socket.gethostname())[0]
    """

    self.MACHINE_NAME = socket.gethostname()
    self.COMPUTER_NAME = self.MACHINE_NAME
    return self.MACHINE_NAME


  def _link(self, src_path, target_subpath, is_dir, target=None):
    """
    Creates a symbolic link.

    Parameters:
    ----------
    src_path: str, mandatory
      Symlink src full path

    target_subpath: str, mandatory
      Subpath in the target directory of the logger

    is_dir: bool, mandatory
      Whether is directory or file

    target: str, optional
      Target directory of the logger (data, models, output or logs)
      The default is None ('data')
    """
    if target is None:
      target = 'data'

    if not os.path.exists(src_path):
      self.verbose_log("ERROR! Could not create symlink, because '{}' does not exist".format(src_path))
      return

    target_path = self.get_target_folder(target)
    if target_path is None:
      return

    target_path = os.path.join(target_path, target_subpath)
    if os.path.exists(target_path):
      return

    target_path_parent = Path(target_path).parent
    if not os.path.exists(target_path_parent):
      os.makedirs(target_path_parent)

    os.symlink(
      src_path, target_path,
      target_is_directory=is_dir
    )

    return

  def link_file(self, src_path, target_subpath, target=None):
    self._link(src_path, target_subpath, is_dir=False, target=target)
    return

  def link_folder(self, src_path, target_subpath, target=None):
    self._link(src_path, target_subpath, is_dir=True, target=target)
    return

  @property
  def is_main_thread(self):
    return threading.current_thread() is threading.main_thread()
  
  @staticmethod
  def get_os_name():
    import platform
    return platform.platform()
    
  @staticmethod
  def get_conda_env():
    folder = os.environ.get("CONDA_PREFIX", None)
    if folder is not None and len(folder) > 0:
      try:
        env = os.path.split(folder)[-1]
      except:
        env = None
    return env

  @staticmethod
  def get_active_git_branch():
    fn = './.git/HEAD'
    if os.path.isfile(fn):
      with open(fn, 'r') as f:
        content = f.readlines()
      for line in content:
        if line.startswith('ref:'):
          return line.partition('refs/heads/')[2].replace('\n','')
    else:
      return None
  
  
  def dict_pretty_format(self, d, indent=4, as_str=True, display_callback=None, display=False): 
    if display and display_callback is None:
      display_callback = self.P
    lst_data = []
    def deep_parse(dct, ind=indent):
      for key, value in dct.items():
        str_key = str(key) if not isinstance(key, str) else "'{}'".format(key)
        lst_data.append(' ' * ind + str(str_key) + ' : ')
        if isinstance(value, dict):
          lst_data[-1] = lst_data[-1] + '{'
          deep_parse(value, ind=ind + indent)
          lst_data.append(' ' * ind + '}')
        else:
          str_value = str(value) if not isinstance(value,str) else "'{}'".format(value)
          lst_data[-1] = lst_data[-1] + str_value
      return
    deep_parse(dct=d,ind=0)
    
    displaybuff = "{\n"
    for itm in lst_data:
      displaybuff += '  ' + itm + '\n'
    displaybuff += "}"
    
    if display_callback is not None:
      displaybuff = "Dict pretty formatter:\n" + displaybuff
      display_callback(displaybuff)
    if as_str:
      return displaybuff
    else:
      return lst_data
      
