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

import os
import subprocess
import json
import requests
import signal

import flask

from functools import partial
from time import sleep

from libraries import Logger
from libraries import LummetryObject
from libraries.logger_mixins.serialization_json_mixin import NPJson
from libraries.model_server_v2.utils import get_api_request_body

__VER__ = '0.1.1.0'

class FlaskGateway(LummetryObject):

  app = None

  def __init__(self, log : Logger,
               server_names,
               workers_location,
               workers_suffix=None,
               host=None,
               port=None,
               first_server_port=None,
               server_execution_path=None,
               **kwargs
              ):

    """
    Parameters:
    -----------
    log : Logger, mandatory

    server_names: List[str], mandatory
      The names of the servers that will be run when the gateway is opened. This names should be names of .py files
      found in `workers_location`

    workers_location: str, mandatory
      Dotted path of the folder where the business logic of the workers is implemented

    workers_suffix: str, optional
      For each worker, which is the suffix of the class name.
      e.g. if the worker .py file is called 'get_similarity.py', then the name of the class is GetSimilarity<Suffix>.
      If `workers_suffix=Worker`; then the name of the class is GetSimilarityWorker
      The default is None

    host: str, optional
      Host of the gateway
      The default is None ('127.0.0.1')

    port: int, optional
      Port of the gateway
      The default is None (5000)

    first_server_port: int, optional
      Port of the first server (the ports are allocated sequentially starting with `first_port_server`)
      The default is None (port+1)

    server_execution_path: str, optional
      The API rule where the worker logic is executed.
      The default is None ('/analyze')
    """

    self.__version__ = __VER__

    self._start_server_names = server_names
    self._host = host or '127.0.0.1'
    self._port = port or 5000
    self._server_execution_path = server_execution_path or '/analyze'
    self._workers_location = workers_location
    self._workers_suffix = workers_suffix

    self._first_server_port = first_server_port or self._port + 1
    self._current_server_port = self._first_server_port

    self._config_endpoints = None

    self._servers = {}
    self._paths = None
    super(FlaskGateway, self).__init__(log=log, prefix_log='[FSKGW]', **kwargs)
    return

  def _log_banner(self):
    _logo = "FlaskGateway v{} started on '{}:{}'".format(
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

  def startup(self):
    super().startup()
    self._log_banner()
    self._config_endpoints = self.config_data.get('CONFIG_ENDPOINTS', {})

    if not self._server_execution_path.startswith('/'):
      self._server_execution_path = '/' + self._server_execution_path

    self.start_servers()

    if self._paths is None:
      self.kill_servers()
      raise ValueError("Gateway cannot start because no paths were retrieved from endpoints.")

    self.app = flask.Flask('FlaskGateway')
    self.app.json_encoder = NPJson
    for rule in self._paths:
      partial_view_func = partial(self._view_func_worker, rule)
      partial_view_func.__name__ = "partial_view_func_{}".format(rule.lstrip('/'))
      self.app.add_url_rule(
        rule=rule,
        view_func=partial_view_func,
        methods=['GET', 'POST', 'OPTIONS']
      )
    #endfor

    self.app.add_url_rule(
      rule='/start_server',
      endpoint='StartServerEndpoint',
      view_func=self._view_func_start_server,
      methods=['GET', 'POST']
    )

    self.app.add_url_rule(
      rule='/kill_server',
      endpoint='KillServerEndpoint',
      view_func=self._view_func_kill_server,
      methods=['GET', 'POST']
    )

    self.app.run(
      host=self._host,
      port=self._port,
      threaded=True
    )
    return

  def _start_server(self, server_name, host, port, execution_path, verbosity=1):
    msg = "Creating server {}@{}:{}{}".format(server_name, host, port, execution_path)
    if verbosity >= 1:
      self.P(msg, color='g')
    else:
      self._create_notification('log', msg)
    #endif

    process = subprocess.Popen([
      'python',
      'libraries/model_server_v2/run_server.py',
      '--base_folder',      self.log.root_folder,
      '--app_folder',       self.log.app_folder,
      '--config_endpoint',  json.dumps(self._config_endpoints.get(server_name, {})),
      '--host',             host,
      '--port',             str(port),
      '--execution_path',   execution_path,
      '--workers_location', self._workers_location,
      '--worker_name',      server_name,
      '--worker_suffix',    self._workers_suffix,
      '--use_tf',
    ])

    self._servers[server_name] = {
      'PID' : process.pid,
      'HOST' : host,
      'PORT' : port
    }

    msg = "Successfully created server {} with PID={}".format(server_name, process.pid)
    if verbosity >= 1:
      self.P(msg, color='g')
    else:
      self._create_notification('log', msg)
    #endif

    sleep(1)
    return

  def _get_paths_from_server(self, server_name):
    self.P("Requesting to server {} in order to get the requests paths".format(server_name))
    url = 'http://{}:{}{}'.format(
      self._servers[server_name]['HOST'],
      self._servers[server_name]['PORT'],
      '/get_paths'
    )

    response = requests.get(url=url)
    self._paths = response.json()['PATHS']
    self.P("  Responded with paths={}".format(self._paths))
    return

  def start_servers(self):
    for i,server_name in enumerate(self._start_server_names):
      self._start_server(
        server_name=server_name,
        host=self._host,
        port=self._current_server_port,
        execution_path=self._server_execution_path,
        verbosity=1
      )
      self._current_server_port += 1

      if self._paths is None:
        self._get_paths_from_server(server_name)

    return

  def _get_server_pid(self, server_name):
    return self._servers[server_name]['PID']

  def _server_exists(self, server_name):
    return server_name in self._servers

  @property
  def active_servers(self):
    return list(self._servers.keys())

  def _kill_server_by_name(self, server_name):
    pid = self._get_server_pid(server_name)
    os.kill(pid, signal.SIGKILL)
    self._servers.pop(server_name)
    return

  def kill_servers(self):
    for server_name in self._servers:
      self._kill_server_by_name(server_name)
    return

  def _view_func_worker(self, path):
    request = flask.request
    params = get_api_request_body(request)
    signature = params.pop('SIGNATURE', None)
    if signature is None:
      return flask.jsonify({'ERROR' : "Bad input. 'SIGNATURE' not found"})

    if signature not in self._servers:
      return flask.jsonify({'ERROR' : "Bad signature {}. Available signatures: {}".format(signature, self.active_servers)})

    url = 'http://{}:{}{}'.format(
      self._servers[signature]['HOST'],
      self._servers[signature]['PORT'],
      path
    )

    response = requests.post(url, data=params)
    return flask.jsonify(response.json())

  def _view_func_start_server(self):
    request = flask.request
    params = get_api_request_body(request)
    signature = params.get('SIGNATURE', None)

    if signature is None:
      return flask.jsonify({'ERROR' : "Bad input. 'SIGNATURE' not found"})

    if self._server_exists(signature):
      return flask.jsonify({'ERROR' : "Signature {} already started".format(signature)})

    self._start_server(
      server_name=signature,
      host=self._host,
      port=self._current_server_port,
      execution_path=self._server_execution_path,
      verbosity=0
    )
    self._current_server_port += 1
    return flask.jsonify({'MESSAGE': 'OK.'})

  def _view_func_kill_server(self):
    request = flask.request
    params = get_api_request_body(request)
    signature = params.get('SIGNATURE', None)

    if signature is None:
      return flask.jsonify({'ERROR' : "Bad input. 'SIGNATURE' not found"})

    if not self._server_exists(signature):
      return flask.jsonify({'ERROR' : "Bad signature {}. Available signatures: {}".format(signature, self.active_servers)})

    pid = self._get_server_pid(signature)
    self._kill_server_by_name(signature)
    return flask.jsonify({'MESSAGE' : 'OK. Killed PID={}'.format(pid)})
