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

from collections import OrderedDict, deque
from time import time as tm
import threading

class _TimersMixin(object):
  """
  Mixin for timers functionalities that are attached to `libraries.logger.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `libraries.logger.Logger`

  In this mixin we can use any attribute/method of the Logger.
  """

  def __init__(self):
    super(_TimersMixin, self).__init__()
    self.timers = None
    self.timer_level = 0
    self.opened_timers = None
    self.timers_graph = None
    self._timer_error = False
    return

  def reset_timers(self):
    self.timers = OrderedDict()
    self._timer_error = False
    self.timers_graph = OrderedDict()
    self.timers_graph["ROOT"] = OrderedDict()
    self.opened_timers = deque()
    self.timer_level = 0
    return

  @staticmethod
  def get_empty_timer():
    return {
      'MEAN': 0,
      'MAX': 0,
      'COUNT': 0,
      'START': 0,
      'END': 0,
      'PASS': True,
      'LEVEL': 0,

      'START_COUNT': 0,
      'STOP_COUNT': 0,
    }

  def restart_timer(self, sname):
    self.timers[sname] = self.get_empty_timer()
    return

  def _add_in_timers_graph(self, sname):
    self.timers[sname]['LEVEL'] = self.timer_level
    self.timers_graph[sname] = OrderedDict() ## there is no ordered set, so we use OrderedDict with no values
    return

  def start_timer(self, sname):
    assert threading.current_thread() is threading.main_thread()

    if not self.DEBUG:
      return -1

    if sname not in self.timers:
      self.restart_timer(sname)

    curr_time = tm()
    self._add_in_timers_graph(sname)
    self.timers[sname]['START'] = curr_time
    self.timers[sname]['START_COUNT'] += 1
    if len(self.opened_timers) >= 1:
      parent = self.opened_timers[-1]
    else:
      parent = "ROOT"
    #endif

    self.timers_graph[parent][sname] = None
    self.timer_level += 1
    self.opened_timers.append(sname)

    if self.timer_level >= 10 and not self._timer_error:
      self.P("Something is wrong with timers:", color='r')
      for ft in self.get_faulty_timers():
        self.P("  {}: {}".format(ft, self.timers[ft]), color='r')
      self._timer_error = True
    #endif

    return curr_time

  def get_time_until_now(self, sname):
    ctimer = self.timers[sname]
    return tm() - ctimer['START']

  def get_faulty_timers(self):
    lst_faulty = []
    for tmr_name, tmr in self.timers.items():
      if (tmr['START_COUNT'] - tmr['STOP_COUNT']) > 1:
        lst_faulty.append(tmr_name)
    return lst_faulty

  def end_timer_no_skip(self, sname):
    return self.end_timer(sname, skip_first_timing=False)

  def end_timer(self, sname, skip_first_timing=True):
    result = 0
    if self.DEBUG:
      self.opened_timers.pop()
      self.timer_level -= 1

      ctimer = self.timers[sname]
      ctimer['STOP_COUNT'] += 1
      ctimer['END'] = tm()
      result = ctimer['END'] - ctimer['START']
      _count = ctimer['COUNT']
      _prev_avg = ctimer['MEAN']
      avg = _count * _prev_avg

      if ctimer['PASS'] and skip_first_timing:
        ctimer['PASS'] = False
        return result  # do not record first timing in average nor the max

      ctimer['MAX'] = max(ctimer['MAX'], result)

      ctimer['COUNT'] = _count + 1
      avg += result
      avg = avg / ctimer["COUNT"]
      ctimer['MEAN'] = avg
    return result

  def stop_timer(self, sname, skip_first_timing=True):
    return self.end_timer(sname=sname, skip_first_timing=skip_first_timing)

  def show_timer_total(self, sname):
    ctimer = self.timers[sname]
    cnt = ctimer['COUNT']
    val = ctimer['MEAN'] * cnt
    self.P("  {} = {:.3f} in {} laps".format(sname, val, cnt))
    return

  def _print_timer(self, key,
                   summary='mean',
                   show_levels=True,
                   show_max=True,
                   show_current=True,
                   div=None
                   ):

    ctimer = self.timers.get(key, None)

    if ctimer is None:
      return

    mean_time = ctimer['MEAN']
    max_time = ctimer['MAX']
    current_time = ctimer['END'] - ctimer['START']
    if show_levels:
      s_key = '  ' * ctimer['LEVEL'] + key
    else:
      s_key = key
    msg = None
    if summary in ['mean', 'avg']:
      # self.verbose_log(" {} = {:.4f}s (max lap = {:.4f}s)".format(s_key,mean_time,max_time))
      msg = " {} = {:.4f}s".format(s_key, mean_time)
    else:
      # self.verbose_log(" {} = {:.4f}s (max lap = {:.4f}s)".format(s_key,total, max_time))
      total = mean_time * ctimer['COUNT']
      msg = " {} = {:.4f}s".format(s_key, total)
    if show_max:
      msg += ", max: {:.4f}s".format(max_time)
    if show_current:
      msg += ", curr: {:.4f}s".format(current_time)
    if div is not None:
      msg += ", itr(B{}): {:.4f}s".format(div, mean_time / div)
    self.verbose_log(msg)
    return

  def show_timers(self, summary=None,
                  title=None,
                  show_levels=True,
                  show_max=True,
                  show_current=True,
                  div=None):

    if summary is None:
      summary = 'mean'

    if title is None:
      title = ''

    def dfs(visited, graph, node):
      if node not in visited:
        self._print_timer(
          key=node,
          summary=summary,
          show_levels=show_levels, show_current=show_current,
          show_max=show_max, div=div
        )
        visited.add(node)
        keys = list(graph[node].keys())
        for neighbour in keys:
          dfs(visited, graph, neighbour)
        #endfor
      #endif
    #enddef

    buffer_visited = set()

    if self.DEBUG:
      if len(title) > 0:
        title = ' ' + title
      self.verbose_log("Timing results{}:".format(title))
      dfs(buffer_visited, self.timers_graph, "ROOT")
    else:
      self.verbose_log("DEBUG not activated!")
    return

  def get_stats(self):
    self.show_timers()
    return

  def show_timings(self):
    self.show_timers()
    return

  def get_timing_dict(self, skey):
    return self.timers[skey] if skey in self.timers else {}

  def get_timer(self, skey):
    return self.get_timing_dict(skey)

  def get_timer_mean(self, skey):
    tmr = self.get_timer(skey)
    result = tmr.get('MEAN', 0)
    return result

  def get_timer_count(self, skey):
    tmr = self.get_timer(skey)
    result = tmr.get('COUNT', 0)
    return result
