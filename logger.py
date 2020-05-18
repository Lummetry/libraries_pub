import os
import sys
import bz2
import json
import shutil
import socket
import codecs
import pickle
import asyncio
import textwrap
import itertools
import numpy as np

from functools import wraps
from time import time as tm
from collections import OrderedDict
from datetime import datetime as dt, timedelta
from io import BytesIO, TextIOWrapper


try: 
  import tensorflow.compat.v1 as tf1
except:
  pass


__VER__ = '1.0.2.3'

_HTML_START = "<HEAD><meta http-equiv='refresh' content='5' ></HEAD><BODY><pre>"
_HTML_END = "</pre></BODY>"

class Logger(object):
  """
  Lummetry Swissknife
  ===================
  The methods in this class are split into groups (blocks) of functionalities which are delimited with comments:
    - start block: <<<<<<<<<<<<<<<<<<<< START <i>. <FunctionalityName> <<<<<<<<<<<<<<<<<<<<
    - end block  : >>>>>>>>>>>>>>>>>>>> END <i>. <FunctionalityName> >>>>>>>>>>>>>>>>>>>>

    FunctionalityName(s):
    1. BaseLogger
      - logging, config_file

    2. General

    3. DataFrame

    4. Serialization

    5. NLP

    6. ComputerVision

    7. LENS

    8. TFKeras

    9. StaticMethods
  """

  def __init__(self, lib_name="",
               lib_ver="",
               config_file="",
               base_folder=".",
               app_folder=".",
               show_time=True,
               config_file_encoding=None,
               no_folders_no_save=False,
               max_lines=None,
               HTML=False,
               DEBUG=True,
               data_folder_additional_configs=None,
               TF_KERAS=True,
               BENCHMARKER=False):
    # <<<<<<<<<<<<<<<<<<<< START 1. BaseLogger <<<<<<<<<<<<<<<<<<<<
    self.__lib__= lib_name
    self.show_time = show_time
    self.no_folders_no_save = no_folders_no_save
    self.max_lines = max_lines
    self.HTML = HTML
    self.DEBUG = DEBUG
    self.log_suffix = lib_name
    self._base_folder = base_folder
    self._app_folder = app_folder
    self.data_folder_additional_configs = data_folder_additional_configs
    
    self.__version__ = __VER__
    self.version = self.__version__
    self.file_prefix = None
    self.refresh_file_prefix()
    self.is_running_from_ipython = self.runs_from_ipython()
    self.is_running_in_debugger = self.runs_with_debugger()
    self.last_time = tm()
    self.app_log = list()
    self.results = list()
    self.printed = list()
    self.split_part = 1
    self.config_data = None
    self.MACHINE_NAME = self.get_machine_name()
    self.log_results_file = self.file_prefix + "_RESULTS.txt"
    self.timers = OrderedDict()
    self.timer_level = 0
    
    self._configure_data_and_dirs(config_file, config_file_encoding)
    self._generate_log_path()
    self._check_additional_configs()
    
    ver = "v.{}".format(lib_ver) if lib_ver != "" else ""
    self.verbose_log("Library [{} {}] initialized on machine [{}]".format(
                      self.__lib__, ver, self.MACHINE_NAME))
    if self.is_running_from_ipython:
      self.verbose_log('  Script running in ipython.')
    if self.is_running_in_debugger:
      self.verbose_log('  Script running in debug mode.')
    # >>>>>>>>>>>>>>>>>>>> END 1. BaseLogger >>>>>>>>>>>>>>>>>>>>



    return

  ###############################################################
  ###############################################################
  ###############################################################
  # <<<<<<<<<<<<<<<<<<<< START 1. BaseLogger <<<<<<<<<<<<<<<<<<<<
  ###############################################################
  ###############################################################
  ###############################################################
  def _logger(self, logstr, show=True, results=False, noprefix=False, show_time=False):
    """
    log processing method
    """
    elapsed = tm() - self.last_time

    self._add_log(logstr, show=show, results=results,
                  noprefix=noprefix,
                  show_time=show_time)

    self._save_log()

    self.last_time = tm()

    self._check_log_size()
    return elapsed
  
  
  def _add_log(self, logstr, show=True, results=False, noprefix=False, show_time=False):
    if type(logstr) != str:
      logstr = str(logstr)
    if logstr == "":
      logstr = " "
    elapsed = tm() - self.last_time
    nowtime = dt.now()
    prefix = ""
    strnowtime = nowtime.strftime("[{}][%Y-%m-%d %H:%M:%S] ".format(self.__lib__))
    if self.show_time and (not noprefix):
      prefix = strnowtime
    if logstr[0]=="\n":
      logstr = logstr[1:]
      prefix = "\n"+prefix
    res_log = logstr
    logstr = prefix + logstr
    if show_time:
      logstr += " [{:.2f}s]".format(elapsed)
    self.app_log.append(logstr)
    if show:
      print("\r" + logstr, flush = True)
      self.printed.append(True)
    else:
      self.printed.append(False)
    if results:
      self.results.append(res_log)
      self.save_results()
    return
  
  
  def _save_log(self, DEBUG_ERRORS=False):
    if self.no_folders_no_save:
      return
    nowtime = dt.now()
    strnowtime = nowtime.strftime("[{}][%Y-%m-%d %H:%M:%S] ".format(self.__lib__))
    stage = 0
    try:
      log_output = codecs.open(self.log_file, "w", "utf-8")  #open(self.log_file, 'w+')
      stage += 1
      if self.HTML:
        log_output.write(_HTML_START)
        stage += 1
        iter_list = reversed(self.app_log)
      else:
        iter_list = self.app_log
      for log_item in iter_list:
        #if self.HTML:
        #  log_output.write("%s<BR>\n" % log_item)
        #else:
          log_output.write("{}\n".format(log_item))
          stage += 1
      if self.HTML:
        log_output.write(_HTML_END)
        stage += 1
      log_output.close()
      stage += 1
    except:
      if DEBUG_ERRORS:
        print(strnowtime+"LogWErr S: {} [{}]".format(stage,
              sys.exc_info()[0]), flush = True)
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
  
  
  def verbose_log(self, str_msg, results=False, show_time=False, noprefix=False):
    return self._logger(str_msg, show=True, results=results, show_time=show_time,
                        noprefix=noprefix)
  def P(self,str_msg, results=False, show_time=False, noprefix=False):
    return self.p(str_msg, results, show_time, noprefix)

  def Pr(self,str_msg, results=False, show_time=False, noprefix=False):
    if type(str_msg) != str:
      str_msg = str(str_msg)
    print("\r" + str_msg, flush=True, end='')

  
  def p(self,str_msg, results=False, show_time=False, noprefix=False):
    return self._logger(str_msg, show=True, results=results, show_time=show_time,
                        noprefix=noprefix)

  def iP(self,str_msg, results=False, show_time=False, noprefix=False):
    if self.is_running_from_ipython:
      return self._logger(str_msg, show=True, results=results, show_time=show_time,
                          noprefix=noprefix)
    return
  
  
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
          results=False, 
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
          results=False, 
          noprefix=False, 
          show_time=False,
          )
      self.print_func('<strong>' + s + '</strong>')
    else:
      self.P(s)
    return  

  def print_pad(self, str_msg, str_text, n=3):
    if type(str_msg) != str:
      str_msg = str(str_msg)
    if type(str_text) != str:
      str_text = str(str_text)
    str_final = str_msg + "\n" +  textwrap.indent(str_text, n * " ")
    self._logger(str_final, show=True, results=False, show_time=False)
    return

  def log(self,str_msg, show = False, results = False, show_time = False):
    return self._logger(str_msg, show=show, results=results, show_time=show_time)

  
  def save_results(self, fn='_results.txt', save_in_logs=True):
    if save_in_logs:
      fn_full = os.path.join(self._logs_dir, fn)
    else:
      fn_full = fn
    nowtime = dt.now()
    strnowtime = nowtime.strftime("[{}][%Y-%m-%d %H:%M:%S] ".format(self.__lib__))
    stage = 0
    try:
      log_output = codecs.open(fn_full, "w", "utf-8")
      stage += 1
      for log_item in self.results:
        log_output.write("{}\n".format(log_item))
        stage += 1
      log_output.close()
      stage += 1
    except:
      print(strnowtime+"ResLogWErr S: {} [{}]".format(stage,
            sys.exc_info()[0]), flush = True)
    return
  
  
  def show_results(self):
    for res in self.results:
      self._logger(res, show = True, noprefix = True)
    return
  
  
  def _generate_log_path(self):
    if self.no_folders_no_save:
      return
    part = '{:03d}'.format(self.split_part)
    lp = self.file_prefix
    ls = self.log_suffix
    if self.HTML:
      self.log_file = lp + '_' + ls + '_' + part +'_log_web.html'
    else:
      self.log_file = lp + '_' + ls + '_' + part + '_log.txt'

    self.log_file = os.path.join(self._logs_dir, self.log_file)
    path_dict = {}
    path_dict['CURRENT_LOG'] = self.log_file
    file_path = os.path.join(self._logs_dir, self.__lib__+'.txt')
    with open(file_path, 'w') as fp:
      json.dump(path_dict, fp, sort_keys=True, indent=4)
    self._add_log("{} log changed to {}...".format(file_path, self.log_file))
    self.log_results_file = os.path.join(self._logs_dir, self.log_results_file)
    return
  
  def _get_cloud_base_folder(self, base_folder):
    if "GOOGLE" in base_folder.upper():
      base_folder = self.get_google_drive()
    if "DROPBOX" in base_folder.upper():
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
      assert ("BASE_FOLDER" in self.config_data.keys())
      assert ("APP_FOLDER" in self.config_data.keys())
      base_folder = self.config_data["BASE_FOLDER"]
      if '~' in base_folder:
        base_folder = base_folder.replace('~', os.path.expanduser("~"))
      app_folder = self.config_data["APP_FOLDER"]
      base_folder = self._get_cloud_base_folder(base_folder)
      self._base_folder  = os.path.join(base_folder,app_folder)
      if not os.path.isdir(self._base_folder):
        try:
          os.mkdir(self._base_folder)
        except:
          raise ValueError("Invalid app base folder '{}'!".format(self._base_folder))
      print("Loaded config [{}]  BASE: {}".format(
          config_file,self._base_folder), flush = True)
      self.config_file = config_file
    else:
      self.config_data = {}
      self._base_folder = self._get_cloud_base_folder(self._base_folder)
      self.config_data['BASE_FOLDER'] = self._base_folder
      self.config_data['APP_FOLDER'] = self._app_folder
      self.config_file = "default_config.txt"
      self._base_folder = os.path.join(self._base_folder, self._app_folder)

    self._logs_dir = os.path.join(self._base_folder,"_logs")
    self._outp_dir = os.path.join(self._base_folder,"_output")
    self._data_dir = os.path.join(self._base_folder,"_data")
    self._modl_dir = os.path.join(self._base_folder,"_models")

    self._setup_folders([self._outp_dir, self._logs_dir, self._data_dir,
                         self._modl_dir])

  
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
    
    data_files = os.listdir(check_dir)
  
    for f in data_files:
      if any(x in f for x in ['config', 'cfg', 'conf']):
        fn = self.get_data_file(f)
        self.P("Found additional config in '{}'".format(fn))
        additional_configs.append(json.load(open(fn), object_pairs_hook=OrderedDict))
    
    if len(additional_configs) > 0:
      dct_final = {}
      for d in additional_configs:
        dct_final.update(d)
      for k,v in dct_final.items():
        if k in self.config_data:
          self.P("[WARNING] Overriding key '{}'".format(k))
        self.config_data[k] = v
    return
  
  
  def raise_error(self, error_message):
    self.P("ERROR: {}".format(error_message))
    raise ValueError(str(error_message))
    
  
  def _default_close_callback(self, sig, frame):
    self.P("SIGINT/Ctrl-C received. Script closing")
    if self._close_callback is None:
      self.P("WARNING: `register_close_callback` received and will force close. Please provide a callback where you can stop the script loop and deallocate nicely.")
      sys.exit(0)
    else:
      self._close_callback()
    return
    
  def register_close_callback(self, func=None):
    """
    will register a SIGINT/Ctrl-C callback or will default to the one in Logger
    """
    import signal
    if func is None:
      self.P("WARNING: register_close_callback received NO callback. The script will not behave nice. Please provide a callback where you can stop the script nicely. ")
    self._close_callback = func
    signal.signal(signal.SIGINT, self._default_close_callback)
    self.P("Registered {} SIGINT/Ctrl-C callback".format('custom' if func else 'default'))
    return
  
  
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

  def get_machine_name(self):
    """
    if socket.gethostname().find('.')>=0:
        name=socket.gethostname()
    else:
        name=socket.gethostbyaddr(socket.gethostname())[0]
    """
    if not hasattr(self, 'MACHINE_NAME'):
      self.MACHINE_NAME = socket.gethostname()
      self.COMPUTER_NAME = self.MACHINE_NAME
    return self.MACHINE_NAME
  
  
  def get_base_folder(self):
    return self._base_folder if hasattr(self, '_base_folder') else ''
  
  def get_data_folder(self):
    return self._data_dir if hasattr(self, '_data_dir') else ''
  
  def get_output_folder(self):
    return self._outp_dir if hasattr(self, '_outp_dir') else ''
  
  def get_models_folder(self):
    return self._modl_dir if hasattr(self, '_modl_dir') else ''

  def get_data_subfolder(self, _dir):
    _data = self.get_data_folder()
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

    raise ValueError('Could not build path')

  def get_root_file(self, str_file):
    fn = os.path.join(self.get_base_folder(), str_file)
    assert os.path.isfile(fn)
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
  
  
  def check_folder(self, sub_folder):
    sfolder = os.path.join(self.get_base_folder(),sub_folder)
    if sfolder not in self.folder_list:
      self.folder_list.append(sfolder)

    if not os.path.isdir(sfolder):
      self.verbose_log(" Creating folder [...{}]".format(sfolder[-40:]))
      os.makedirs(sfolder)
    return sfolder


  def show_not_printed(self):
    nr_log = len(self.app_log)
    for i in range(nr_log):
      if not self.printed[i]:
        print(self.app_log[i], flush = True)
        self.printed[i] = True
    return
  
  
  def start_timer(self, sname):
    if not self.DEBUG:
      return -1

    count_key = sname+"___COUNT"
    start_key = sname+"___START"
    pass_key  = sname+"___PASS"
    level_key = sname+"___level"
    if not (count_key in self.timers.keys()):
      self.timers[count_key] = 0
      self.timers[sname] = 0
      self.timers[pass_key] = True
      self.timers[level_key] = self.timer_level
    ctime = tm()
    self.timers[start_key] = ctime
    self.timer_level += 1
    return ctime

  def stop_timer(self, sname, skip_first_timing = True):
    return self.end_timer(sname, skip_first_timing)

  def end_timer(self, sname, skip_first_timing = True):
    result = 0
    if self.DEBUG:
      self.timer_level -= 1
      count_key = sname+"___COUNT"
      start_key = sname+"___START"
      end_key   = sname+"___END"
      pass_key  = sname+"___PASS"

      self.timers[end_key] = tm()
      result = self.timers[end_key] - self.timers[start_key]
      _count = self.timers[count_key]
      _prev_avg = self.timers[sname]
      avg =  _count *  _prev_avg

      if self.timers[pass_key] and skip_first_timing:
        self.timers[pass_key] = False
        return result # do not record first timing in average

      self.timers[count_key] = _count + 1
      avg += result
      avg = avg / self.timers[sname+"___COUNT"]
      self.timers[sname] = avg
    return result


  def show_timer_total(self, key):
    cnt = self.timers[key+"___COUNT"]
    val = self.timers[key] * cnt
    self.P("  {} = {:.3f} in {} laps".format(key, val, cnt))
    return

  def show_timers(self, summary='mean'):
    if self.DEBUG:
      self.verbose_log("Timing results:")
      for key,val in self.timers.items():
        if not ("___" in key):
          level_key = key + "___level"
          s_key = '  ' * self.timers[level_key] + key
          if summary in ['mean', 'avg']:
            self.verbose_log(" {} = {:.3f}s".format(s_key,val))
          else:
            total = val * self.timers[key+"___COUNT"]
            self.verbose_log(" {} = {:.3f}s".format(s_key,total))            
    else:
      self.verbose_log("DEBUG not activated!")
    return


  def get_stats(self):
    self.show_timers()
    return
  
  def show_timings(self):
    self.show_timers()
    return
    
  def get_timing(self, skey):
    return self.timers[skey] if skey in self.timers else 0

  def get_timer(self, skey):
    return self.get_timing(skey)
  
  def maybe_download_model(self, url, model_file, force_download=False, url_model_cfg=None):
    """
    url11 = 'https://www.dropbox.com/s/t6qfxiopcr8yvlq/60_xomv_employee01_002_e142_acc0.985.pb?dl=1'
    url12 = 'https://www.dropbox.com/s/akzyk9vcuqluzup/60_xomv_employee01_002_e142_acc0.985.pb.txt?dl=1'
    # use maybe_download_model
    log.maybe_download_model(url11, 'model1_dup.pb', 
                             force_download=False, 
                             url_model_cfg=url12)
    """
    urls = [url]
    fn = [model_file]
    if url_model_cfg is not None:
      urls += [url_model_cfg]
      fn += [model_file + '.txt']
    return self.maybe_download(url=urls,
                               fn=fn,
                               force_download=force_download,
                               target='models'
                               )

    
  def maybe_download(self, 
                     url, 
                     fn=None, 
                     force_download=False,
                     target='models'):
    """
    will (maybe) download a from a given (full) url a file and save to 
    target folder in `model_file`
    
    Examples:
      
    url11 = 'https://www.dropbox.com/s/t6qfxiopcr8yvlq/60_xomv_employee01_002_e142_acc0.985.pb?dl=1'
    fn1 = 'model1.pb'
    url12 = 'https://www.dropbox.com/s/akzyk9vcuqluzup/60_xomv_employee01_002_e142_acc0.985.pb.txt?dl=1'
    fn2 = 'model1.txt'
    url21 = 'https://www.dropbox.com/s/tuywpfzv6ueknj6/70_xfgc03_007_e092_acc0.9413.pb?dl=1'
    fn3 = 'model2.pb'
    url22 = 'https://www.dropbox.com/s/5wrvohffl14qfd3/70_xfgc03_007_e092_acc0.9413.pb.txt?dl=1'
    fn4 = 'model2.txt'
    log = Logger(lib_name='MDL',  config_file='config/duplex_config.txt',  TF_KERAS=False)
    
    # download two files in output 
    log.maybe_download(url=[url11, url12],
                       fn=[fn1,fn2],
                       target='output'
                       )
    
    # download a txt in data
    log.maybe_download(url=url12,
                       fn='model1_dup.txt',
                       target='data'
                       )
    
    # download another two files in models with other signature
    log.maybe_download(url={
                        fn3 : url21,
                        fn4 : url22
                        },
                       force_download=True,
                       target='models'
                       )
    
    # use maybe_download_model
    log.maybe_download_model(url11, 'model1_dup.pb', 
                             force_download=False, 
                             url_model_cfg=url12)    
      
    """
    import urllib
    assert target in ['models','data','output'], "target must be either 'models', 'data' or 'output'"

    if type(url) is dict:
      urls = [v for k,v in url.items()]
      fns = [k for k in url]
    else:
      if fn is None:
        self.raise_error("fn must be a string or a list if url param does not have file:url dict")
      urls = url
      fns = fn
      if type(urls) is str:
        urls = [urls]
      if type(fns)  is str:
        fns = [fns]
      if len(fns) != len(urls):
        self.raise_error("must provided same nr of urls and file names")
    
    self.P("Checking and (maybe) downloading `{}` file(s) {}".format(
        target, fns))
    
    def _print_download_progress(count, block_size, total_size):
      """
      Function used for printing the download progress.
      Used as a call-back function in maybe_download_and_extract().
      """
    
      # Percentage completion.
      pct_complete = float(count * block_size) / total_size
    
      # Limit it because rounding errors may cause it to exceed 100%.
      pct_complete = min(1.0, pct_complete)
    
      # Status-message. Note the \r which means the line should overwrite itself.
      msg = "\r- Download progress: {0:.1%}".format(pct_complete)
    
      # Print it.
      sys.stdout.write(msg)
      sys.stdout.flush()
      return  

    # Path for local file.
    if target == 'models':
      download_dir = self.get_models_folder()
    elif target == 'data':
      download_dir = self.get_data_folder()
    elif target == 'output':
      download_dir = self.get_output_folder()
    else:
      self.raise_error("Unknown target {}".format(target))
    
    saved_files = []
    msgs = []
    for _fn,_url in zip(fns, urls):
      save_path = os.path.join(download_dir, _fn)
      # Check if the file already exists, otherwise we need to download it now.
      has_file = os.path.exists(save_path)
      if not has_file or force_download:
        # Check if the download directory exists, otherwise create it.
        if not os.path.exists(download_dir):
          self.P("Download folder not found - creating")
          os.makedirs(download_dir)
        if has_file:
          self.P("Forced download: removing ...{}".format(save_path[-40:]))
          os.remove(save_path)
    
        # Download the file from the internet.
        self.P("Downloading {} from {}...".format(_fn, _url[:40]))
        file_path, msg = urllib.request.urlretrieve(url=_url,
                                                    filename=save_path,
                                                    reporthook=_print_download_progress)
        saved_files.append(file_path)
        msgs.append(msg)
        print("", flush=True)
        self.P("Download done and saved in ...{}".format(file_path[-40:]))
        #endif
      else:
        self.P("File {} found. Skipping.".format(_fn))
    return saved_files, msgs
    
  def expand_tilda(self, path):
    if '~' in path:
      path = path.replace('~', os.path.expanduser('~'))
    return path
  
  def refresh_file_prefix(self):
    self.file_prefix = dt.now().strftime("%Y%m%d_%H%M%S")
    return
  
  def now_str(self):
    return dt.now().strftime("%Y%m%d%H%M%S%f")

  #############################################################
  #############################################################
  #############################################################
  # >>>>>>>>>>>>>>>>>>>> END 1. BaseLogger >>>>>>>>>>>>>>>>>>>>
  #############################################################
  #############################################################
  #############################################################


  ############################################################
  ############################################################
  ############################################################
  # <<<<<<<<<<<<<<<<<<<< START 2. General <<<<<<<<<<<<<<<<<<<<
  ############################################################
  ############################################################
  ############################################################

  def tqdm_enumerate(self, _iter):
    from tqdm import tqdm
    i = 0
    for y in tqdm(_iter):
      yield i, y
      i += 1

  def show_histogram(self, data, bins=10, caption=None, non_negative_only=True,
                     show_both_ends=False):
    return self.show_text_histogram(data, bins,
                                    caption, non_negative_only,
                                    show_both_ends)

  def show_text_histogram(self, data, bins=10, caption=None, non_negative_only=True,
                          show_both_ends=False):
    """
    displays a text histogram of input 1d array
    """
    hist = True
    data = np.array(data)
    if ('u' in data.dtype.str) or ('i' in data.dtype.str):
      hist = False

    if caption is None:
      caption = ''

    if hist:
      caption += " - Histogram"
    else:
      caption += ' - Bin-count'

    if hist:
      res = np.histogram(data, bins=bins)
      y_inp = res[0]
      x_inp = res[1]
      x_format = '{num:{fill}{width}.3f}'
    else:
      x_format = '{num:{fill}{width}.0f}'
      res = np.bincount(data)
      _min = data.min()
      _max = data.max()
      y_inp = res[_min:]
      x_inp = np.arange(_min, _max + 1)
      if non_negative_only:
        non_neg = (y_inp != 0)
        y_inp = y_inp[non_neg]
        x_inp = x_inp[non_neg]
      if bins < y_inp.shape[0]:
        if not show_both_ends:
          cutoff = bins // 2
          caption += ' (showing both {} ends)'.format(cutoff)
          y_inp = np.concatenate((y_inp[:cutoff], y_inp[-cutoff:]))
          x_inp = np.concatenate((x_inp[:cutoff], x_inp[-cutoff:]))
      else:
        show_both_ends = False

    bins = y_inp.shape[0] if bins > y_inp.shape[0] else bins
    _x = []
    _y = []
    if show_both_ends:
      self.P("{} first ({} bins):".format(caption, bins))
      for i in range(bins):
        _y.append('{num:{fill}{width}.0f}'.format(num=y_inp[i], fill=' ', width=8))
        _x.append(x_format.format(num=x_inp[i], fill=' ', width=8))
      self.P("    Y: " + ''.join([y for y in _y]))
      self.P("    X: " + ''.join([x for x in _x]))
      _x = []
      _y = []
      self.P("{} last ({} bins):".format(caption, bins))
      for i in range(x_inp.shape[0] - bins, x_inp.shape[0], 1):
        _y.append('{num:{fill}{width}.0f}'.format(num=y_inp[i], fill=' ', width=8))
        _x.append(x_format.format(num=x_inp[i], fill=' ', width=8))
      self.P("    Y: " + ''.join([y for y in _y]))
      self.P("    X: " + ''.join([x for x in _x]))
    else:
      self.P("{} ({} bins):".format(caption, bins))
      for i in range(bins):
        _y.append('{num:{fill}{width}.0f}'.format(num=y_inp[i], fill=' ', width=8))
        _x.append(x_format.format(num=x_inp[i], fill=' ', width=8))
      self.P("    Y: " + ''.join([y for y in _y]))
      self.P("    X: " + ''.join([x for x in _x]))
    return res

  def reset_seeds(self, seed=123):
    """
    this method resets all possible random seeds in order to ensure
    reproducible results
    this method resets for:
        numpy, random, tensorflow, torch
    """
    _np = self.package_loader('numpy', return_package=True)
    _rn = self.package_loader('random', return_package=True)
    _tf = self.package_loader('tensorflow', return_package=True)
    _tc = self.package_loader('torch', return_package=True)
    if _np is not None:
      self.P("Setting random seed {} for 'Numpy'".format(seed))
      _np.random.seed(seed)
    if _rn is not None:
      self.P("Setting random seed {} for 'random'".format(seed))
      _rn.seed(seed)
    if _tf is not None:
      self.P("Setting random seed {} for 'tensorflow'".format(seed))
      if _tf.__version__[0] == '2':
        _tf.random.set_seed(seed)
      else:
        _tf.set_random_seed(seed)
    if _tc is not None:
      self.P("Setting random seed {} for 'torch'".format(seed))
      _tc.manual_seed(seed)
    return

  def plot_confusion_matrix(self, cm, classes=["0", "1"],
                            normalize=True,
                            title='Confusion matrix',
                            no_save=False,
                            cmap=None):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    if normalize:
      cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
      s_title = "[Normalized] " + title
    else:
      s_title = "[Standard] " + title

    import matplotlib.pyplot as plt
    if cmap is None:
      cmap = plt.cm.Blues
    plt.figure()
    plt.imshow(cm, cmap=cmap, interpolation='nearest')
    plt.colorbar()

    tick_marks = np.arange(start=-1, stop=cm.shape[0] + 1)
    lbs = [''] + classes + ['']
    plt.xticks(ticks=tick_marks, labels=lbs, rotation=45)
    plt.yticks(ticks=tick_marks, labels=lbs)

    plt.title(s_title)

    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
      num = "{:.2f}".format(cm[i, j]) if normalize else cm[i, j]
      plt.text(j, i, num,
               horizontalalignment="center",
               color="white" if cm[i, j] > thresh else "black")

    #    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    if not no_save:
      _lbl = s_title.replace(" ", "_").lower()
      self.save_plot(plt, label=_lbl, include_prefix=False, just_label=True)
    plt.show()
    return

  def log_confusion_matrix(self,
                           cm,
                           classes=["0", "1"],
                           title='Confusion Matrix',
                           normalize=None,
                           hide_zeroes=False,
                           hide_diagonal=False,
                           hide_threshold=None,
                           ):
    """pretty print for confusion matrixes"""
    labels = classes
    columnwidth = max([len(x) for x in labels] + [8])  # 5 is value length
    empty_cell = " " * columnwidth
    full_str = "         " + empty_cell + "Preds\n"
    n_classes = cm.shape[0]
    if len(labels) != n_classes:
      self.raise_error("Confusion matrix classes differ from number of labels")
    if n_classes > 2:
      max_lab = max([len(x) for x in labels])
      s1 = "  {:>" + str(max_lab) + "}"
      self.P("{} class breakdown:".format(title))
      self.P((s1 + " {:>7} {:>7} [{:>7} {:>7} {:>7}]").format(
        " " * max_lab,
        "TP",
        "GT",
        "REC",
        "PRE",
        "F1"
      ))
      f1scores = []
      for i, k in enumerate(labels):
        tp = cm[i, i]
        fp = cm[:, i].sum() - tp
        gt = cm[i].sum()
        rec = tp / gt
        pre = tp / (tp + fp)
        f1 = 2 * (pre * rec) / (pre + rec)
        f1scores.append(f1)
        self.P((s1 + ":{:>7}/{:>7} [{:>6.1f}% {:>6.1f}% {:>6.1f}%]").format(
          k, tp, gt, rec * 100, pre * 100, f1 * 100))
      f1macro = np.mean(f1scores)
      self.P("  Macro F1: {:.2f}%".format(f1macro * 100))
    if normalize is None:
      if cm.shape[0] > 2:
        normalize = True
      else:
        normalize = False

    if normalize:
      cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    full_str += "    " + empty_cell + " "
    for label in labels:
      full_str += "%{0}s".format(columnwidth) % label + " "
    full_str += "\n"
    # Print rows
    for i, label1 in enumerate(labels):
      if i == 0:
        full_str += "GT  %{0}s".format(columnwidth) % label1 + " "
      else:
        full_str += "    %{0}s".format(columnwidth) % label1 + " "
      for j in range(len(labels)):
        num = round(cm[i, j], 2) if normalize else cm[i, j]
        cell = '{num:{fill}{width}}'.format(num=num, fill=' ', width=columnwidth)
        # "%{0}.0f".format(columnwidth) % cm[i, j]
        if hide_zeroes:
          cell = cell if float(cm[i, j]) != 0 else empty_cell
        if hide_diagonal:
          cell = cell if i != j else empty_cell
        if hide_threshold:
          cell = cell if cm[i, j] > hide_threshold else empty_cell
        full_str += cell + " "
      full_str += "\n"
    self.P("{}:\n{}".format(title, full_str))
    return

  def save_plot(self, plt, label='', include_prefix=True, just_label=False,
                full_path=None):
    """
    saves current figure to file
    """
    _, short_file = self.output_pyplot_image(plt=plt,
                                             label=label,
                                             include_prefix=include_prefix,
                                             just_label=just_label,
                                             full_path=full_path)
    return short_file

  def output_pyplot_image(self, plt, label='', include_prefix=True,
                          use_single_prefix=True,
                          just_label=False,
                          full_path=None):
    """
    saves current figure to a file
    """
    if full_path is None:
      if include_prefix:
        file_prefix = dt.now().strftime("%Y%m%d_%H%M%S")
        if use_single_prefix:
          file_prefix = self.file_prefix
        part_file_name = "FIG_{}_{}{}".format(file_prefix, label, ".png")
      else:
        file_prefix = ""
        part_file_name = "{}{}".format(label, ".png")

      file_name = os.path.join(self._outp_dir, part_file_name)
    else:
      file_name = full_path

    _folder, _fn = os.path.split(file_name)
    self.verbose_log("Saving pic '{}' in [..{}]".format(_fn, _folder[-30:]))
    plt.savefig(file_name)
    return file_name, _fn

  def output_image(self, arr, label=''):
    """
    saves array to a file as image
    """
    label = label.replace(">", "_")
    file_prefix = dt.now().strftime("%Y%m%d_%H%M%S_")
    if ".png" not in label:
      label += '.png'
    file_name = os.path.join(self._outp_dir, file_prefix + label)
    self.verbose_log("Saving {} to figure [...{}]".format(
      arr.shape, file_name[-40:]))
    if os.path.isfile(file_name):
      self.verbose_log("Aborting image saving. File already exists.")
    else:
      import matplotlib.pyplot as plt
      plt.imsave(file_name, arr)
    return file_name

  def save_image(self, **kwargs):
    return self.output_image(**kwargs)

  @staticmethod
  def plot_histogram(distributions, colors=None, legends=None, figsize=None, dpi=None, bins=None,
                     logscale=False, xticks=None, rotation_xticks=None, title=None,
                     xlabel=None, ylabel=None, save_img_path=None,
                     close_fig=False, save_fig_pickle=False):
    """
    - distributions: should be a list, where each element in the list is a distribution
                     that will be plotted
    - colors: list which specifies the colors (as string) for each distribution
    """
    import seaborn as sns
    import matplotlib.pyplot as plt
    assert type(distributions) == list

    if legends:
      assert type(legends) == list
      assert len(distributions) == len(legends)

    if colors:
      assert type(colors) == list
      assert len(distributions) == len(colors)
    else:
      colors = ['blue'] * len(distributions)

    if figsize: figsize = (figsize[0] / dpi, figsize[1] / dpi)
    fig = plt.figure(figsize=figsize, dpi=dpi)

    for i, distribution in enumerate(distributions):
      plot = sns.distplot(distribution, hist=True, kde=False,
                          bins=bins, color=colors[i], hist_kws={'edgecolor': 'black'})

    if legends: plt.legend(legends)
    if logscale: plot.set_yscale('log')
    if xticks is not None:
      plot.set(xticks=xticks)
      if rotation_xticks is not None: plt.xticks(rotation=rotation_xticks)
    if title is not None:  plot.set_title(title)
    if xlabel is not None: plot.set(xlabel=xlabel)
    if ylabel is not None: plot.set(ylabel=ylabel)

    if save_img_path is not None:
      if not save_img_path.endswith('.png'):
        save_img_path += '.png'
      fig.savefig(save_img_path)
      if save_fig_pickle:
        with open(save_img_path + '.pickle', 'wb') as handle:
          pickle.dump(fig, handle, protocol=pickle.HIGHEST_PROTOCOL)

    if close_fig: plt.close()
    return

  ### embeddings util functions - both LENS and ALLAN

  @staticmethod
  def _measure_changes(Y, Y_prev):
    """
    this helper function measures changes in the embedding matrix
    between previously step of the retrofiting loop and the current one
    """
    return np.abs(np.mean(np.linalg.norm(
      np.squeeze(Y_prev) - np.squeeze(Y),
      ord=2)))



  ##########################################################
  ##########################################################
  ##########################################################
  # >>>>>>>>>>>>>>>>>>>> END 2. General >>>>>>>>>>>>>>>>>>>>
  ##########################################################
  ##########################################################
  ##########################################################


  ##############################################################
  ##############################################################
  ##############################################################
  # <<<<<<<<<<<<<<<<<<<< START 3. DataFrame <<<<<<<<<<<<<<<<<<<<
  ##############################################################
  ##############################################################
  ##############################################################

  def load_dataframe(self, fn, timestamps=None, folder='data'):
    """
    if fn ends in ".zip" then the loading will also uncompress in-memory
    """
    import pandas as pd

    assert folder in [None, 'data', 'output', 'models']
    if folder == 'data':
      lfld = self._data_dir
    elif folder == 'output':
      lfld = self._outp_dir
    elif folder == 'models':
      lfld = self._modl_dir

    if folder is not None:
      datafile = os.path.join(lfld, fn)
      self.verbose_log("Loading CSV '{}' from '{}'".format(fn, folder))
    else:
      datafile = fn
      self.verbose_log("Loading CSV '{}'".format(fn))
      
    ext = os.path.splitext(datafile)[-1]
    file_path = datafile
    self.P("Loading datframe '{}'...".format(datafile))
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

  def load_output_dataframe(self, fn, timestamps=None):
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

  def load_abs_dataframe(self, fn, timestamps=None):
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

  def save_dataframe(self, df, fn='', show_prefix=False, 
                     folder='data',
                     ignore_index=True, compress=False,
                     mode='w', header=True,
                     to_data=None,
                     full_path=None,
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
    if folder == 'data' or to_data:
      lfld = self._data_dir
    elif folder == 'output':
      lfld = self._outp_dir
    elif folder == 'models':
      lfld = self._modl_dir
    elif folder is None:
      lfld = None
      

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
    return file_name, out_file

  def save_dataframe_current_time(self, df, fn=''):
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

  def save_dataframe_to_hdf(self, df, h5_file, h5_format='table'):
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

  def load_dataframe_from_hdf(self, h5_file):
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

  ############################################################
  ############################################################
  ############################################################
  # >>>>>>>>>>>>>>>>>>>> END 3. DataFrame >>>>>>>>>>>>>>>>>>>>
  ############################################################
  ############################################################
  ############################################################



  ##################################################################
  ##################################################################
  ##################################################################
  # <<<<<<<<<<<<<<<<<<<< START 4. Serialization <<<<<<<<<<<<<<<<<<<<
  ##################################################################
  ##################################################################
  ##################################################################

  def load_json(self, fn, folder=None):
    assert folder in [None, 'data', 'output', 'models']
    if folder == 'data':
      lfld = self._data_dir
    elif folder == 'output':
      lfld = self._outp_dir
    elif folder == 'models':
      lfld = self._modl_dir

    if folder is not None:
      datafile = os.path.join(lfld, fn)
      self.verbose_log("Loading json '{}' from '{}'".format(fn, folder))
    else:
      datafile = fn
      self.verbose_log("Loading json '{}'".format(fn))

    if os.path.isfile(datafile):
      with open(datafile) as f:
        data = json.load(f)
      return data
    else:
      self.verbose_log("  File not found!")

  def load_dict(self, **kwargs):
    return self.load_json(**kwargs)

  def load_data_json(self, fname):
    return self.load_json(fname, folder='data')

  def save_data_json(self, data_json, fname):
    datafile = os.path.join(self._data_dir, fname)
    self.verbose_log('Saving data json: {}'.format(datafile))
    with open(datafile, 'w') as fp:
      json.dump(data_json, fp, sort_keys=True, indent=4)
    return datafile

  def load_output_json(self, fname):
    return self.load_json(fname, folder='output')

  def save_output_json(self, data_json, fname):
    datafile = os.path.join(self._outp_dir, fname)
    self.verbose_log('Saving output json: {}'.format(datafile))
    with open(datafile, 'w') as fp:
      json.dump(data_json, fp, sort_keys=True, indent=4)
    return datafile

  def load_models_json(self, fname):
    return self.load_json(fname, folder='models')

  def save_models_json(self, data_json, fname):
    datafile = os.path.join(self._modl_dir, fname)
    self.verbose_log('Saving models json: {}'.format(datafile))
    with open(datafile, 'w') as fp:
      json.dump(data_json, fp, sort_keys=True, indent=4)
    return datafile

  def load_dict_from_data(self, fn):
    return self.load_data_json(fn)

  def load_dict_from_models(self, fn):
    return self.load_models_json(fn)

  def load_dict_from_output(self, fn):
    return self.load_output_json(fn)

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

  def save_pickle(self, data, fn, folder='data',
                  use_prefix=False, verbose=True,
                  compressed=False):
    """
    compressed: True if compression is required OR you can just add '.pklz' to `fn`
    """

    if folder == 'data':
      lfld = self._data_dir
    elif folder == 'output':
      lfld = self._outp_dir
    elif folder == 'models':
      lfld = self._modl_dir
    else:
      raise ValueError("Uknown save folder '{}' - valid options are data, output, models".format(
        folder))
    if use_prefix:
      fn = self.file_prefix + '_' + fn
    datafile = os.path.join(lfld, fn)
    if compressed or '.pklz' in fn:
      if not compressed:
        self.P("Saving pickle with compression=True forced due to extension")
      else:
        self.P("Saving pickle with compression...")
      if self._save_compressed_pickle(datafile, myobj=data):
        self.P("  Compressed pickle {} saved in {}".format(fn, folder))
      else:
        self.P("  FAILED compressed pickle save!")
    else:
      self.P("Saving uncompressed pickle {} in {}".format(fn, folder))
      with open(datafile, 'wb') as fhandle:
        pickle.dump(data, fhandle, protocol=pickle.HIGHEST_PROTOCOL)
      if verbose:
        self.P("  Saved pickle '{}' in '{}' folder".format(
          fn, folder))
    return datafile

  def save_pickle_to_data(self, data, fn, compressed=False):
    """
    compressed: True if compression is required OR you can just add '.pklz' to `fn`
    """
    return self.save_pickle(data, fn, folder='data', compressed=compressed)

  def save_pickle_to_models(self, data, fn, compressed=False):
    """
    compressed: True if compression is required OR you can just add '.pklz' to `fn`
    """
    return self.save_pickle(data, fn, folder='models', compressed=compressed)

  def save_pickle_to_output(self, data, fn, compressed=False):
    """
    compressed: True if compression is required OR you can just add '.pklz' to `fn`
    """
    return self.save_pickle(data, fn, folder='output', compressed=compressed)

  def load_pickle_from_models(self, fn, decompress=False):
    """
     decompressed : True if the file was saved with `compressed=True` or you can just use '.pklz'
    """
    return self.load_pickle(fn, folder='models', decompress=decompress)

  def load_pickle_from_data(self, fn, decompress=False):
    """
     decompressed : True if the file was saved with `compressed=True` or you can just use '.pklz'
    """
    return self.load_pickle(fn, folder='data', decompress=decompress)

  def load_pickle_from_output(self, fn, decompress=False):
    """
     decompressed : True if the file was saved with `compressed=True` or you can just use '.pklz'
    """
    return self.load_pickle(fn, folder='output', decompress=decompress)

  def load_pickle(self, fn, folder='data', decompress=False):
    """
     load_from: 'data', 'output', 'models'
     decompressed : True if the file was saved with `compressed=True` or you can just use '.pklz'
    """
    if folder == 'data':
      lfld = self._data_dir
    elif folder == 'output':
      lfld = self._outp_dir
    elif folder == 'models':
      lfld = self._modl_dir
    else:
      raise ValueError("Uknown load folder '{}' - valid options are data, output, models".format(
        folder))
    datafile = os.path.join(lfld, fn)
    self.verbose_log("Loading pickle '{}' from '{}'".format(fn, folder))
    data = None
    if os.path.isfile(datafile):
      if decompress or '.pklz' in datafile:
        if not decompress:
          self.P("Loading pickle with decompress=True forced due to extension")
        else:
          self.P("Loading pickle with decompression...")
        data = self._load_compressed_pickle(datafile)
      else:
        with open(datafile, "rb") as f:
          data = pickle.load(f)
      if data is None:
        self.P("  Pickle load failed!")
      else:
        self.P("  Pickle loaded.")
    else:
      self.P("  File not found! Pickle load failed.")
    return data

  def save_csr(self, fn, csr_matrix, folder='data', use_prefix=True, verbose=True):
    from scipy import sparse
    if folder == 'data':
      lfld = self._data_dir
    elif folder == 'output':
      lfld = self._outp_dir
    elif folder == 'models':
      lfld = self._modl_dir
    else:
      raise ValueError("Uknown save folder '{}' - valid options are `data`, `output`, `models`".format(
        folder))
    if use_prefix:
      fn = self.file_prefix + '_' + fn
    datafile = os.path.join(lfld, fn)
    sparse.save_npz(datafile, csr_matrix)
    if verbose:
      self.P("Saved sparse csr matrix '{}' in '{}' folder".format(
        fn, folder))
    return

  def load_csr(self, fn, folder='data'):
    """
     load_from: 'data', 'output', 'models'
    """
    from scipy import sparse
    if folder == 'data':
      lfld = self._data_dir
    elif folder == 'output':
      lfld = self._outp_dir
    elif folder == 'models':
      lfld = self._modl_dir
    else:
      raise ValueError("Uknown load folder '{}' - valid options are data, output, models".format(
        folder))
    datafile = os.path.join(lfld, fn)
    self.verbose_log("Loading csr sparse matrix '{}' from '{}'".format(fn, folder))
    data = None
    if os.path.isfile(datafile):
      data = sparse.load_npz(datafile)
    else:
      self.P("  File not found!")
    return data


  def save_np(self, fn, arr_or_arrs, folder='data', use_prefix=True, verbose=True):
    if folder == 'data':
      lfld = self._data_dir
    elif folder == 'output':
      lfld = self._outp_dir
    elif folder == 'models':
      lfld = self._modl_dir
    else:
      raise ValueError("Uknown save folder '{}' - valid options are `data`, `output`, `models`".format(
        folder))
    if use_prefix:
      fn = self.file_prefix + '_' + fn
    datafile = os.path.join(lfld, fn)
    if type(arr_or_arrs) == list:
      np.savez(datafile, arr_or_arrs)
    elif type(arr_or_arrs) == np.ndarray:
      np.save(datafile, arr_or_arrs)
    else:
      raise ValueError("Unknown `arr_or_arrs` - must provide either list of ndarrays or a single ndarray")
    if verbose:
      self.P("Saved sparse numpy data '{}' in '{}' folder".format(
        fn, folder))
    return



  def load_np(self, fn, folder='data'):
    """
     `folder`: 'data', 'output', 'models'
    """
    if folder == 'data':
      lfld = self._data_dir
    elif folder == 'output':
      lfld = self._outp_dir
    elif folder == 'models':
      lfld = self._modl_dir
    else:
      raise ValueError("Uknown load folder '{}' - valid options are data, output, models".format(
        folder))
    datafile = os.path.join(lfld, fn)
    self.verbose_log("Loading numpy data '{}' from '{}'".format(fn, folder))
    data = None
    if os.path.isfile(datafile):
      data = np.load(datafile)
    else:
      self.P("  File not found!")
    return data


  def read_from_path(self, path):
    import pandas as pd
    from os.path import splitext
    file_name, extension = splitext(path)
    if extension == '.csv':
      self.P('Reading from {}'.format(path))
      df = pd.read_csv(path)
      self.P('Done reading from {}'.format(path), show_time=True)
      return df
    elif extension == '.xls' or extension == '.xlsx':
      self.P('Reading from {}'.format(path))
      df = pd.read_excel(path)
      self.P('Done reading from {}'.format(path), show_time=True)
      return df
    elif extension == '.pkl':
      self.P('Reading from {}'.format(path))
      with open(path, 'rb') as handle:
        df = pickle.load(handle)
      self.P('Done reading from {}'.format(path), show_time=True)
      return df
    raise ValueError('Extension {} not understood!'.format(extension))

  def write_to_path(self, path, data):
    import pandas as pd
    from os.path import splitext
    file_name, extension = splitext(path)
    if extension == '.csv':
      if isinstance(data, np.ndarray):
        data = pd.DataFrame(data)
      data.to_csv(path, index=False)
    elif extension == '.xls' or extension == '.xlsx':
      if isinstance(data, np.ndarray):
        data = pd.DataFrame(data)
      data.to_excel(path, index=False)
    elif extension == '.pkl':
      with open(path, 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)

  def save_dict_txt(self, path, dct):
    json.dump(dct, open(path, 'w'), sort_keys=True, indent=4)
    return

  def load_dict_txt(self, path):
    with open(path) as f:
      data = json.load(f)
    return data

  ################################################################
  ################################################################
  ################################################################
  # >>>>>>>>>>>>>>>>>>>> END 4. Serialization >>>>>>>>>>>>>>>>>>>>
  ################################################################
  ################################################################
  ################################################################


  ############################################################
  ############################################################
  ############################################################
  # <<<<<<<<<<<<<<<<<<<< START 8. TFKeras <<<<<<<<<<<<<<<<<<<<
  ##################################################################
  ##################################################################
  ##################################################################
  
  
  def get_gpu(self):    
    res = []
    try:
      from tensorflow.python.client import device_lib
      loc = device_lib.list_local_devices()
      res = [x.physical_device_desc for x in loc if x.device_type == 'GPU']
    except:
      pass
    return res

  def load_tf_graph(self, pb_file):
    
    self.verbose_log("Prep graph from [...{}]...".format(pb_file[-30:]))
    detection_graph = None
    if os.path.isfile(pb_file):

      start_time = tm()
      detection_graph = tf1.Graph()
      with detection_graph.as_default():
        od_graph_def = tf1.GraphDef()
        with tf1.io.gfile.GFile(pb_file, 'rb') as fid:
          serialized_graph = fid.read()
          od_graph_def.ParseFromString(serialized_graph)
          tf1.import_graph_def(od_graph_def, name='')
      end_time = tm()
      self.verbose_log("Done preparing graph in {:.2f}s.".format(end_time - start_time))
    else:
      self.verbose_log(" FILE NOT FOUND [...{}]...".format(pb_file[-30:]))
    return detection_graph


  def load_graph_from_models(self, model_name, get_input_output=False):
    if model_name[-3:] != '.pb':
      model_name += '.pb'
    graph_file = os.path.join(self.get_models_folder(), model_name)
    tf_graph = self.load_tf_graph(graph_file)
    if get_input_output:
      cfg = self.load_models_json(graph_file + '.txt')
      s_input = cfg['INPUT_0']
      s_output = cfg['OUTPUT_0']
      return tf_graph, s_input, s_output
    else:
      return tf_graph
    
  def combine_graphs_tf1(self, lst_graphs, lst_names):
    """
    will return a graph that combines all given graphs
    individual tensors of graph `i` in `lst_graphs` can be accessed via
    `lst_names[i] + '/TENSOR_NAME'.
    """

    assert len(lst_graphs) == len(lst_names)
    gdefs = []
    for graph in lst_graphs:
      gdefs.append(graph.as_graph_def())
    full_graph = tf1.Graph()
    self.P("Creating one graph out of {} graphs: {}".format(len(lst_graphs), lst_names))
    with full_graph.as_default():
      for gdef, gname in zip(gdefs, lst_names):
        self.P("  Adding {}".format(gname))
        tf1.import_graph_def(graph_def=gdef, name=gname)
    return full_graph
    


  ##########################################################
  ##########################################################
  ##########################################################
  # >>>>>>>>>>>>>>>>>>>> END 8. TFKeras >>>>>>>>>>>>>>>>>>>>
  ##########################################################
  ##########################################################
  ##########################################################



  ##################################################################
  ##################################################################
  ##################################################################
  # <<<<<<<<<<<<<<<<<<<< START 9. StaticMethods <<<<<<<<<<<<<<<<<<<<
  ##################################################################
  ##################################################################
  ##################################################################
  @staticmethod
  def runs_from_ipython():
    try:
      __IPYTHON__
      return True
    except NameError:
      return False

  @staticmethod
  def runs_with_debugger():
    gettrace = getattr(sys, 'gettrace', None)
    if gettrace is None:
      return False
    else:
      return not gettrace() is None

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
  def sliding_window(data, size, stepsize=1, padded=False, axis=-1, copy=True):
    """
    Calculate a sliding window over a signal
    Parameters
    ----------
    data : numpy array
        The array to be slided over.
    size : int
        The sliding window size
    stepsize : int
        The sliding window stepsize. Defaults to 1.
    axis : int
        The axis to slide over. Defaults to the last axis.
    copy : bool
        Return strided array as copy to avoid sideffects when manipulating the
        output array.
    Returns
    -------
    data : numpy array
        A matrix where row in last dimension consists of one instance
        of the sliding window.
    Notes
    -----
    - Be wary of setting `copy` to `False` as undesired sideffects with the
      output values may occurr.
    Examples
    --------
    >>> a = numpy.array([1, 2, 3, 4, 5])
    >>> sliding_window(a, size=3)
    array([[1, 2, 3],
           [2, 3, 4],
           [3, 4, 5]])
    >>> sliding_window(a, size=3, stepsize=2)
    array([[1, 2, 3],
           [3, 4, 5]])
    See Also
    --------
    pieces : Calculate number of pieces available by sliding
    """
    if axis >= data.ndim:
      raise ValueError(
        "Axis value out of range"
      )

    if stepsize < 1:
      raise ValueError(
        "Stepsize may not be zero or negative"
      )

    if size > data.shape[axis]:
      raise ValueError(
        "Sliding window size may not exceed size of selected axis"
      )

    shape = list(data.shape)
    shape[axis] = np.floor(data.shape[axis] / stepsize - size / stepsize + 1).astype(int)
    shape.append(size)

    strides = list(data.strides)
    strides[axis] *= stepsize
    strides.append(data.strides[axis])

    strided = np.lib.stride_tricks.as_strided(
      data, shape=shape, strides=strides
    )

    if copy:
      return strided.copy()
    else:
      return strided

  @staticmethod
  def get_object_params(obj, n=None):
    """
    Parameters
    ----------
    obj : any type
      the inspected object.
    n : int, optional
      the number of params that are returned. The default is None
      (all params returned).

    Returns
    -------
    out_str : str
      the description of the object 'obj' in terms of parameters values.
    """

    out_str = obj.__class__.__name__ + "("
    n_added_to_log = 0
    for _iter, (prop, value) in enumerate(vars(obj).items()):
      if type(value) in [int, float, bool]:
        out_str += prop + '=' + str(value) + ','
        n_added_to_log += 1
      elif type(value) in [str]:
        out_str += prop + "='" + value + "',"
        n_added_to_log += 1

      if n is not None and n_added_to_log >= n:
        break
    # endfor

    out_str = out_str[:-1] if out_str[-1] == ',' else out_str
    out_str += ')'
    return out_str

  @staticmethod
  def set_nice_prints(linewidth=500,
                      precision=2,
                      np_precision=None,
                      df_precision=None,
                      suppress=False):
    import pandas as pd

    if np_precision is None:
      np_precision = precision
    if df_precision is None:
      df_precision = precision
    np.set_printoptions(precision=np_precision)
    np.set_printoptions(floatmode='fixed')
    np.set_printoptions(linewidth=linewidth)
    np.set_printoptions(suppress=suppress)
    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)
    pd.set_option('display.max_colwidth', 1000)
    _format = '{:.' + str(df_precision) + 'f}'
    pd.set_option('display.float_format', lambda x: _format.format(x))
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
    drop_root = Logger.get_dropbox_drive()
    full = os.path.join(drop_root, sub_folder)
    if os.path.isdir(full):
      return full
    else:
      return None

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
      size += sum([Logger.get_obj_size(v, seen) for v in obj.values()])
      size += sum([Logger.get_obj_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
      size += Logger.get_obj_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
      size += sum([Logger.get_obj_size(i, seen) for i in obj])

    return size

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

  @staticmethod
  def package_loader(package_name, as_bool=True, return_package=False):
    """
    returns True (or nr of similar loaded packages) for a certain package
    if `return_package` == True then returns a reference to the module
    """
    i_res = sum([package_name in x for x in list(sys.modules.keys())])
    if return_package:
      if i_res > 0:
        return sys.modules[package_name]
      else:
        return None
    else:
      if as_bool:
        return i_res > 0
      else:
        return i_res

  @staticmethod
  def grid_plot_images(images, labels, is_matrix=False):
    import matplotlib.pyplot as plt
    n_images = len(images)
    rows = np.round(np.sqrt(n_images))
    columns = rows + 1 * (n_images != rows ** 2)
    fig = plt.figure(figsize=(columns * 3, rows * 3))
    axs = []
    for i in range(len(images)):
      ax = fig.add_subplot(rows, columns, i + 1)
      axs.append(ax)
      if is_matrix:
        ax.matshow(images[i])
      else:
        ax.imshow(images[i])
      ax.set_title(labels[i])
    plt.show()

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
  def get_current_process_memory(mb=True):
    import psutil
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / pow(1024, 2 if mb else 3)
    return mem

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
  def idx_to_proba(idx, thr_50, thr_0):
    """
    Transforms indexes to probabilities.
    Params:
      thr_50: the index for which the probability is 0.5
      thr_0 : the index for which the probability is 0

    a1 * 0 + b1 = 1
    a1 * thr_50 + b1 = 0.5

    a2 * thr_50 + b2 = 0.5
    a2 * thr_0 + b2 = 0
    """

    b1 = 1
    a1 = -0.5 / thr_50

    a2 = 0.5 / (thr_50 - thr_0)
    b2 = -a2 * thr_0

    if type(idx) in [int, float, np.int16, np.int32, np.int64, np.float32, np.float64]:
      idx = [idx]
    if type(idx) is list:
      idx = np.array(idx)

    idx = idx * 1.0
    wh_50 = np.where(idx <= thr_50)
    wh_0 = np.where((idx > thr_50) & (idx <= thr_0))
    idx[wh_50] = a1 * idx[wh_50] + b1
    idx[wh_0] = a2 * idx[wh_0] + b2
    if thr_0 < idx.max():
      wh_abs_0 = np.where((idx > thr_0) & (idx <= idx.max()))
      idx[wh_abs_0] = 0

    return idx

  @staticmethod
  def timestamp_begin(ts, begin_of):
    """returns a new timestamp as if it were the start of minute/hour/day/week/month/year"""
    if ts is None:
      ts = dt.now()
    # endif
    if begin_of == 'minute':
      ts = dt(year=ts.year,
                    month=ts.month,
                    day=ts.day,
                    hour=ts.hour,
                    minute=ts.minute,
                    second=0)
    elif begin_of == 'hour':
      ts = dt(year=ts.year,
                    month=ts.month,
                    day=ts.day,
                    hour=ts.hour,
                    minute=0,
                    second=0)
    elif begin_of == 'day':
      ts = dt(year=ts.year,
                    month=ts.month,
                    day=ts.day,
                    hour=0,
                    minute=0,
                    second=0)
    elif begin_of == 'month':
      ts = dt(year=ts.year,
                    month=ts.month,
                    day=1,
                    hour=0,
                    minute=0,
                    second=0)
    elif begin_of == 'year':
      ts = dt(year=ts.year,
                    month=1,
                    day=1,
                    hour=0,
                    minute=0,
                    second=0)
    # endif
    return ts

  @staticmethod
  def split_time_intervals(start, stop, seconds_interval):
    """splits a predefined timeinterval [start, stop] into smaller intervals
    each of length seconds_interval.
    the method returns a list of dt tuples intervals"""
    lst = []
    _start = None
    _stop = start
    while _stop <= stop:
      _start = _stop
      _stop = _start + timedelta(seconds=seconds_interval)
      lst.append((_start, _stop))
    # endwhile
    return lst
  
  @staticmethod
  def background(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
      loop = asyncio.get_event_loop()
      if callable(f):
        return loop.run_in_executor(None, f, *args, **kwargs)
      else:
        raise TypeError('Task must be a callable')    
      #endif
    return wrapped

  ################################################################
  ################################################################
  ################################################################
  # >>>>>>>>>>>>>>>>>>>> END 9. StaticMethods >>>>>>>>>>>>>>>>>>>>
  ################################################################
  ################################################################
  ################################################################

