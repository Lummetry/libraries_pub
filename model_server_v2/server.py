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

import flask
import numpy as np
from time import sleep

from threading import Lock

from libraries import Logger
from libraries import LummetryObject
from libraries import _PluginsManagerMixin
from libraries.logger_mixins.serialization_json_mixin import NPJson

__VER__ = '0.1.0.2'

class FlaskModelServer(LummetryObject, _PluginsManagerMixin):

  app = None

  def __init__(self, log : Logger,
               plugins_location,
               plugin_name,
               plugin_suffix=None,
               host=None,
               port=None,
               endpoint_name=None,
               verbosity_level=1,
               nr_workers=None
               ):
    self.__version__ = __VER__
    self.__plugins_location = plugins_location
    self.__plugin_name = plugin_name
    self.__plugin_suffix = plugin_suffix
    self.__initial_nr_workers = nr_workers or 5

    self._host = host or '127.0.0.1'
    self._port = port or 5000
    self._endpoint_name = endpoint_name or '/analyze'
    self._verbosity_level = verbosity_level

    self._lst_workers = []
    self._mask_workers_in_use = []
    self._counter = 0

    self._lock = Lock()

    super(FlaskModelServer, self).__init__(log=log, prefix_log='[FSKSVR]', maxlen_notifications=1000)
    return

  def startup(self):
    super().startup()
    self._log_banner()
    self._update_nr_workers(self.__initial_nr_workers)

    self.app = flask.Flask('FlaskModelServer')
    self.app.json_encoder = NPJson
    self.app.add_url_rule(
      rule=self._endpoint_name,
      endpoint="PluginEndpoint",
      view_func=self._view_func_plugin_endpoint,
      methods=['GET', 'POST', 'OPTIONS']
    )

    self.app.add_url_rule(
      rule='/notifications',
      endpoint='NotificationsEndpoint',
      view_func=self._view_func_notifications_endpoint,
      methods=['GET', 'POST']
    )

    self.app.add_url_rule(
      rule='/update_workers',
      endpoint='WorkersEndpoint',
      view_func=self._view_func_workers_endpoint,
      methods=['GET', 'POST'],
    )

    self.app.run(
      host=self._host,
      port=self._port,
      threaded=True
    )

    return

  def _log_banner(self):
    _logo = "FlaskModelServer v{} started on '{}:{}'".format(
      self.__version__, self._host, self._port
    )

    lead = 5
    _logo = " " * lead + _logo
    s2 = (len(_logo) + lead) * "*"
    self.log.P("")
    self.log.P(s2)
    self.log.P("")
    self.log.P(_logo)
    self.log.P("")
    self.log.P(s2)
    self.log.P("")
    return

  def _create_worker(self):
    _module_name, _class_name, _cls_def, _config_dict = self._get_module_name_and_class(
      plugins_location=self.__plugins_location,
      name=self.__plugin_name,
      suffix=self.__plugin_suffix
    )

    if _cls_def is None:
      return

    worker = _cls_def(
      log=self.log,
      default_config=_config_dict,
      verbosity_level=self._verbosity_level
    )
    self._lst_workers.append(worker)
    self._mask_workers_in_use.append(0)
    return

  def _update_nr_workers(self, nr_workers):
    nr_crt_workers = len(self._lst_workers)
    nr_new_workers = nr_workers - nr_crt_workers

    if nr_new_workers > 0:
      for _ in range(nr_new_workers):
        self._create_worker()
      str_msg = "Created {} new workers. (were:{}, total:{})".format(nr_new_workers, nr_crt_workers, nr_workers)
      self._create_notification(notification_type='log', notification=str_msg)
    elif nr_new_workers < 0:
      ###TODO delete only unused
      str_msg = "Should delete {} - not implemented yet".format(-1*nr_new_workers)
      self._create_notification(notification_type='log', notification=str_msg)
    else:
      str_msg = "Update with no effect, there are already {} workers".format(nr_workers)
      self._create_notification(notification_type='log', notification=str_msg)
    #endif
    return

  def _mask_worker_locked(self, wid):
    self._mask_workers_in_use[wid] = 1
    return

  def _mask_worker_unlocked(self, wid):
    self._mask_workers_in_use[wid] = 0

  def _find_unlocked_worker(self):
    self._lock.acquire()
    unlocked_workers = np.where(np.array(self._mask_workers_in_use) == 0)[0]

    if unlocked_workers.shape[0] == 0:
      return

    wid = int(np.random.choice(unlocked_workers))
    self._mask_worker_locked(wid)
    self._lock.release()
    return wid

  def _wait_predict(self, data):
    wid = self._find_unlocked_worker()
    if wid is None:
      # All model servers in use. Waiting...

      while wid is None:
        sleep(1)
        wid = self._find_unlocked_worker()
      #endwhile

      # Waiting done.
    #endif

    # now worker is locked...
    worker = self._lst_workers[wid]
    answer = worker.execute(
      inputs=data,
      counter=self._counter
    )
    self._mask_worker_unlocked(wid)
    return worker, answer, wid


  def _get_request_body(self, request):
    method    = request.method
    args_data = request.args
    form_data = request.form
    json_data = request.json

    if method == 'GET':
      # parameters in URL
      base_params = args_data
    else:
      # parameters in form
      base_params = form_data
      if len(base_params) == 0:
        # params in json?
        base_params = json_data
    #endif

    if base_params is not None:
      params = dict(base_params)
    else:
      params = {}
    #endif

    return params

  def _view_func_plugin_endpoint(self):
    self._counter += 1
    request = flask.request
    method = request.method

    params = self._get_request_body(request=request)
    client = params.get('client', 'unk')

    self._create_notification(
      notification_type='log',
      notification=(self._counter, "Received '{}' request {} from client '{}' params: {}".format(
        method, self._counter, client, params
      ))
    )

    worker, wid = None, -1
    if method != 'OPTIONS':
      worker, answer, wid = self._wait_predict(data=params)
    else:
      answer = {}

    if answer is None:
      jresponse = flask.jsonify({
        "ERROR": "input json does not contain right info or other error has occured",
        "client": client,
        "call_id": self._counter,
        "input": params
      })
    else:
      if isinstance(answer, dict):
        answer['call_id'] = self._counter
        if worker:
          answer['signature'] = '{}:{}'.format(worker.__class__.__name__, wid)
        jresponse = flask.jsonify(answer)
      else:
        assert isinstance(answer, str)
        jresponse = flask.make_response(answer)
      #endif
    #endif

    jresponse.headers["Access-Control-Allow-Origin"] = "*"
    jresponse.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS, DELETE"
    jresponse.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return jresponse

  def _view_func_notifications_endpoint(self):
    server_notifs = self.get_notifications()
    workers_notifs = self.log.flatten_2d_list([w.get_notifications() for w in self._lst_workers])

    all_notifs = server_notifs + workers_notifs

    lst_general_notifs = []
    dct_notifs_per_call = {}
    for notif in all_notifs:
      dct = {
        'NOTIF_TYPE' : notif['NOTIFICATION_TYPE'],
        'MODULE' : notif['MODULE'],
        'TIME'   : notif['TIMESTAMP']
      }

      if isinstance(notif['NOTIFICATION'], tuple):
        counter, msg = notif['NOTIFICATION']
        counter = str(counter)
        dct['NOTIF'] = msg

        if counter not in dct_notifs_per_call:
          dct_notifs_per_call[counter] = []

        dct_notifs_per_call[counter].append(dct)
      elif isinstance(notif['NOTIFICATION'], str):
        msg = notif['NOTIFICATION']
        dct['NOTIF'] = msg
        lst_general_notifs.append(dct)
      #endif

    #endfor

    jresponse = flask.jsonify({
      **{"GENERAL" : lst_general_notifs},
      **dct_notifs_per_call
    })
    return jresponse

  def _view_func_workers_endpoint(self):
    request = flask.request
    params = self._get_request_body(request=request)

    nr_workers = params.get('nr_workers', None)
    if nr_workers is None:
      return flask.jsonify({'message' : 'bad input'})

    self._update_nr_workers(nr_workers)
    return flask.jsonify({'message': 'ok'})
