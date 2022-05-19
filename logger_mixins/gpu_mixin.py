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

import traceback
import platform

class _GPUMixin(object):
  """
  Mixin for GPU functionalities that are attached to `libraries.logger.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `libraries.logger.Logger`

  In this mixin we can use any attribute/method of the Logger.

  * Obs: This mixin uses also attributes/methods of `_MachineInfoMixin`:
    - self.get_machine_memory
    - self.get_avail_memory
  """

  def __init__(self):
    super(_GPUMixin, self).__init__()

    try:
      from .machine_mixin import _MachineMixin
    except ModuleNotFoundError:
      raise ModuleNotFoundError("Cannot use _GPUMixin without having _MachineMixin")

    self._done_first_smi_error = False
    return

  @staticmethod
  def clear_gpu_memory():
    try:
      import tensorflow as tf
      import gc
      gc.collect()
      tf.keras.backend.clear_session()
    except:
      pass
    try:
      import torch as th
      import gc
      gc.collect()
      th.cuda.empty_cache()
      th.cuda.clear_memory_allocated()
    except:
      pass

  @staticmethod
  def get_gpu_memory_map():
    import subprocess
    """Get the current gpu usage.

    Returns
    -------
    usage: dict
        Keys are device ids as integers.
        Values are memory usage as integers in MB.
    """
    result = subprocess.check_output(
      [
        'nvidia-smi', '--query-gpu=memory.used',
        '--format=csv,nounits,noheader'
      ])
    result = result.decode('utf-8')
    # Convert lines into a dictionary
    gpu_memory = [int(x) for x in result.strip().split('\n')]
    gpu_memory_map = dict(zip(range(len(gpu_memory)), gpu_memory))
    return gpu_memory_map

  def gpu_info(self, show=False, mb=False):

    try:
      # first get name
      import torch as th      
    except:
      self.P("ERROR: PyTorch not installed! Please install Pytorch.")
      return None

    nvsmires = None
    try:
      from pynvml.smi import nvidia_smi
      nvsmi = nvidia_smi.getInstance()
      nvsmires = nvsmi.DeviceQuery('memory.free, memory.total, memory.used, utilization.gpu, temperature.gpu')
      pynvml_avail = True
    except:
      pynvml_avail = False

    lst_inf = []
    # now we iterate all devices
    n_gpus = th.cuda.device_count()
    if n_gpus > 0:
      th.cuda.empty_cache()
    for device_id in range(n_gpus):
      dct_device = {}
      device_props = th.cuda.get_device_properties(device_id)
      dct_device['NAME'] = device_props.name
      dct_device['TOTAL_MEM'] = round(
        device_props.total_memory / 1024 ** (2 if mb else 3), 
        2
        )
      mem_total = None
      mem_allocated = None
      gpu_used = None
      gpu_temp = None 
      gpu_temp_max = None
      if pynvml_avail and nvsmires is not None and 'gpu' in nvsmires:
        dct_gpu = nvsmires['gpu'][device_id]
        mem_total = round(
          dct_gpu['fb_memory_usage']['total'] / (1 if mb else 1024), 
          2
          )  # already from th
        mem_allocated = round(
          dct_gpu['fb_memory_usage']['used'] / (1 if mb else 1024), 
          2
          )
        gpu_used = dct_gpu['utilization']['gpu_util']
        if isinstance(gpu_used, str):
          gpu_used = -1
        gpu_temp = dct_gpu['temperature']['gpu_temp']
        gpu_temp_max = dct_gpu['temperature']['gpu_temp_max_threshold']
      else:
        str_os = platform.platform()
        ## check if platform is Tegra and record
        if 'tegra' in str_os.lower():
          # we just record the overall fre memory
          mem_total = self.get_machine_memory()
          mem_allocated = mem_total  - self.get_avail_memory()
          gpu_used = 1
          gpu_temp = 1
          gpu_temp_max = 100
          if not self._done_first_smi_error and nvsmires is not None:
            self.P("Running `gpu_info` on Tegra platform: {}".format(nvsmires), color='r')
            self._done_first_smi_error = True
        elif not self._done_first_smi_error:
          str_err = traceback.format_exc()
          self.P("ERROR: Please make sure you have both pytorch and pynvml in order to monitor the GPU")
          self.P("  Exception info:\n{}".format(str_err))
          self._done_first_smi_error = True
      # end try
      dct_device['ALLOCATED_MEM'] = mem_allocated
      dct_device['FREE_MEM'] = 'N/A'
      if all(x is not None for x in [mem_total, mem_allocated]):
        dct_device['FREE_MEM'] = round(mem_total - mem_allocated,2)
      dct_device['MEM_UNIT'] = 'MB' if mb else 'GB'
      dct_device['GPU_USED'] = gpu_used
      dct_device['GPU_TEMP'] = gpu_temp
      dct_device['GPU_TEMP_MAX'] = gpu_temp_max

      lst_inf.append(dct_device)
    # end for all devices
    if show:
      self.P("GPU information for {} device(s):".format(len(lst_inf)), color='y')
      for dct_gpu in lst_inf:
        for k, v in dct_gpu.items():
          self.P("  {:<14} {}".format(k + ':', v), color='y')
    return lst_inf