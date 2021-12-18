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

import abc

from libraries import Logger
from libraries import LummetryObject
from libraries import _PluginMergeDefaultAndUpstreamConfigs

class FlaskWorker(LummetryObject, _PluginMergeDefaultAndUpstreamConfigs):

  """
  Base class for any worker / endpoint business logic
  """

  def __init__(self, log : Logger,
               default_config,
               verbosity_level,
               upstream_config=None,
               **kwargs):

    """
    Parameters:
    -----------
    log : Logger, mandatory

    default_config: dict, mandatory
      The default configuration of the worker.
      See `libraries.model_server_v2.server -> create_worker` to see the entire flow; it calls `_get_module_name_and_class`
      and searches for a `_CONFIG` in the module with the implementation and passes the value of `_CONFIG` as `default_config`

    verbosity_level: int, mandatory
      A threshold that controls the verbosity - can use it in any implementation

    upstream_config: dict, optional
      The upstream configuration that comes from a configuration file of the process; this `upstream_config` is merged with `default_config`
      in order to compute the final config
      The default is None ({})
    """

    self._default_config = default_config
    self._upstream_config_params = upstream_config or {}
    self.config_worker = None

    self._verbosity_level = verbosity_level

    self._counter = None
    self.__encountered_error = None
    super(FlaskWorker, self).__init__(log=log, maxlen_notifications=1000, **kwargs)
    return

  def startup(self):
    super().startup()
    self.config_worker = self._merge_prepare_config()
    self._load_model()
    return

  @abc.abstractmethod
  def _load_model(self):
    """
    Implement this method in sub-class - custom logic for loading the model. If the worker has no model, then implement
    it as a simple `return`.
    """
    raise NotImplementedError

  @abc.abstractmethod
  def _pre_process(self, inputs):
    """
    Implement this method in sub-class - custom logic for pre-processing the inputs that come from the user

    Parameters:
    -----------
    inputs: dict, mandatory
      The request json

    Returns:
    -------
    prep_inputs:
      Any object that will be used in `_predict` implementation
    """
    raise NotImplementedError

  @abc.abstractmethod
  def _predict(self, prep_inputs):
    """
    Implement this method in sub-class - custom logic for predict

    Parameters:
    -----------
    prep_inputs:
      Any object returned by `_pre_process`

    preds:
      Any object that will be used in `_post_process` implementation
    """
    raise NotImplementedError

  @abc.abstractmethod
  def _post_process(self, pred):
    """
    Implement this method in sub-class - custom logic for post processing the predictions
    (packing the output that goes to the end-user)

    Parameters:
    ----------
    pred:
      Any object returned by `_predict`

    answer: dict
      The answer that goes to the end-user
    """
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
    if prep_inputs is None:
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
    if pred is None:
      return

    try:
      answer = self._post_process(pred)
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
    """
    The method exposed for execution.

    Parameters:
    ----------
    inputs: dict, mandatory
      The request json

    counter: int, mandatory
      The call id

    Returns:
    --------
    answer: dict
      The answer that goes to the end-user
    """
    self.start_timer('execute')
    self._counter = counter
    self.__encountered_error = None

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
    notification = (self._counter or "INIT", notification)
    super()._create_notification(notification_type=notification_type, notification=notification)
    return
