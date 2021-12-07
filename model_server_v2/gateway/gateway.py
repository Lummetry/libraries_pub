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

import subprocess
import json
import requests

import flask

from functools import partial
from time import sleep

from libraries import Logger
from libraries import LummetryObject
from libraries.logger_mixins.serialization_json_mixin import NPJson
from libraries.model_server_v2.request_utils import get_api_request_body

__VER__ = '0.1.2.5'

DEFAULT_NR_WORKERS = 5
DEFAULT_HOST = '127.0.0.1'

class FlaskGateway(LummetryObject):

  app = None

  def __init__(self, log : Logger,
               workers_location,
               server_names=None,
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

    workers_location: str, mandatory
      Dotted path of the folder where the business logic of the workers is implemented

    server_names: List[str], optional
      The names of the servers that will be run when the gateway is opened. This names should be names of .py files
      found in `workers_location`
      The default is None (it takes all the keys in 'CONFIG_ENDPOINTS')

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

    if self._start_server_names is None:
      self._start_server_names = list(self._config_endpoints.keys())

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

  def _start_server(self, server_name, port, execution_path, host=None, nr_workers=None, verbosity=1):
    config_endpoint = self._config_endpoints.get(server_name, {})

    if 'HOST' in config_endpoint:
      host = config_endpoint.pop('HOST')
    else:
      host = host or DEFAULT_HOST
      self.P("WARNING: 'HOST' not provided in endpoint configuration for {}.".format(server_name), color='r')
    #endif

    if 'NR_WORKERS' in config_endpoint:
      nr_workers = config_endpoint.pop('NR_WORKERS')
    else:
      nr_workers = nr_workers or DEFAULT_NR_WORKERS
      self.P("WARNING: 'NR_WORKERS' not provided in endpoint configuration for {}.".format(server_name), color='r')
    #endif

    msg = "Creating server {}@{}:{}{}".format(server_name, host, port, execution_path)
    if verbosity >= 1:
      self.P(msg, color='g')
    else:
      self._create_notification('log', msg)
    #endif

    popen_args = [
      'python',
      'libraries/model_server_v2/run_server.py',
      '--base_folder', self.log.root_folder,
      '--app_folder', self.log.app_folder,
      '--config_endpoint', json.dumps(config_endpoint),
      '--host', host,
      '--port', str(port),
      '--execution_path', execution_path,
      '--workers_location', self._workers_location,
      '--worker_name', server_name,
      '--worker_suffix', self._workers_suffix,
      '--nr_workers', str(nr_workers),
      '--use_tf',
    ]

    process = subprocess.Popen(popen_args)

    self._servers[server_name] = {
      'PROCESS' : process,
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
        port=self._current_server_port,
        execution_path=self._server_execution_path,
        verbosity=1
      )
      self._current_server_port += 1
    #endfor

    nr_tries = 0
    svr = self._start_server_names[0]
    while True:
      try:
        nr_tries += 1
        self._get_paths_from_server(svr)
        break
      except:
        if nr_tries >= 1000:
          raise ValueError("Could not get paths from server {}".format(svr))
        sleep(1)
      #end try-except
    #endwhile

    return

  def _get_server_process(self, server_name):
    return self._servers[server_name]['PROCESS']

  def _server_exists(self, server_name):
    return server_name in self._servers

  @property
  def active_servers(self):
    return list(self._servers.keys())

  def _kill_server_by_name(self, server_name):
    process = self._get_server_process(server_name)
    process.terminate()
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

    response = requests.post(url, json=params)
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

    process = self._get_server_process(signature)
    self._kill_server_by_name(signature)
    return flask.jsonify({'MESSAGE' : 'OK. Killed PID={} with return_code {}.'.format(
      process.pid,
      process.returncode
    )})
