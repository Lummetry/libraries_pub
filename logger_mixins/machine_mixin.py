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

import socket

class _MachineMixin(object):
  """
  Mixin for machine functionalities that are attached to `libraries.logger.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `libraries.logger.Logger`

  In this mixin we can use any attribute/method of the Logger.
  """

  def __init__(self):
    super(_MachineMixin, self).__init__()
    return

  @staticmethod
  def get_platform():
    import platform
    system = platform.system()
    release = platform.release()
    return system, release

  @staticmethod
  def get_cpu_usage():
    import psutil
    cpu = psutil.cpu_percent()
    return cpu

  @staticmethod
  def get_total_disk(gb=True):
    import psutil
    hdd = psutil.disk_usage('/')
    total_disk = hdd.total / ((1024**3) if gb else 1)
    return total_disk

  @staticmethod
  def get_avail_memory(gb=True):
    from psutil import virtual_memory
    avail_mem = virtual_memory().available / ((1024**3) if gb else 1)
    return avail_mem

  @staticmethod
  def get_avail_disk(gb=True):
    import psutil
    hdd = psutil.disk_usage('/')
    avail_disk = hdd.free / ((1024**3) if gb else 1)
    return avail_disk

  @staticmethod
  def get_machine_memory(gb=True):
    from psutil import virtual_memory
    total_mem = virtual_memory().total / ((1024**3) if gb else 1)
    return total_mem