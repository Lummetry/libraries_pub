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
@author: Lummetry.AI - Laurentiu
@project: 
@description:
"""

import abc

from libraries import Logger
from libraries import LummetryObject

class FlaskWorker(LummetryObject):

  def __init__(self, log : Logger, default_config, verbosity_level, **kwargs):
    self.config_worker = default_config
    self._verbosity_level = verbosity_level

    self._counter = None
    self.__encountered_error = None
    super(FlaskWorker, self).__init__(log=log, maxlen_notifications=1000, **kwargs)
    return

  def startup(self):
    super().startup()
    self._load_model()
    return

  @abc.abstractmethod
  def _load_model(self):
    raise NotImplementedError

  @abc.abstractmethod
  def _pre_process(self, inputs):
    raise NotImplementedError

  @abc.abstractmethod
  def _predict(self, prep_inputs):
    raise NotImplementedError

  @abc.abstractmethod
  def _post_process(self, pred):
    raise NotImplementedError

  @staticmethod
  def __err_dict(err_type, err_file, err_func, err_line, err_msg):
    return {
      'ERR_TYPE' : err_type,
      'ERR_MSG' : err_msg,
      'ERR_FILE' : err_file,
      'ERR_FUNC' : err_func,
      'ERR_LINE' : err_line
    }


  def __pre_process(self, inputs):
    try:
      prep_inputs = self._pre_process(inputs)
    except:
      err_dict = self.__err_dict(*self.log.get_error_info(return_err_val=True))
      self.__encountered_error = err_dict['ERR_MSG']
      self._create_notification(
        notification_type='exception',
        notification='Exception in _pre_process:\n{}'.format(err_dict)
      )
      return

    return prep_inputs

  def __predict(self, prep_inputs):
    if not prep_inputs:
      return

    try:
      pred = self._predict(prep_inputs)
    except:
      err_dict = self.__err_dict(*self.log.get_error_info(return_err_val=True))
      self.__encountered_error = err_dict['ERR_MSG']
      self._create_notification(
        notification_type='exception',
        notification='Exception in _predict:\n{}'.format(err_dict)
      )
      return

    return pred

  def __post_process(self, pred):
    if not pred:
      return

    try:
      answer = self._post_process(pred)
      ### TODO add meta info - semnatura microserviciului;
    except:
      err_dict = self.__err_dict(*self.log.get_error_info(return_err_val=True))
      self.__encountered_error = err_dict['ERR_MSG']
      self._create_notification(
        notification_type='exception',
        notification='Exception in _post_process\n{}'.format(err_dict)
      )
      return

    return answer

  def execute(self, inputs, counter):
    self.start_timer('execute')
    self._counter = counter

    self.start_timer('pre_process')
    prep_inputs = self.__pre_process(inputs)
    self.end_timer('pre_process')

    self.start_timer('predict')
    pred = self.__predict(prep_inputs)
    self.end_timer('predict')

    self.start_timer('post_process')
    answer = self.__post_process(pred)
    self.end_timer('post_process')

    self.end_timer('execute')

    if self.__encountered_error:
      answer = {'ERROR' : self.__encountered_error}

    return answer

  def _create_notification(self, notification_type, notification):
    notification = (self._counter, notification)
    super()._create_notification(notification_type=notification_type, notification=notification)
    return
