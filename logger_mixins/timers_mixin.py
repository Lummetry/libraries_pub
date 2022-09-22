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
import numpy as np

from collections import OrderedDict, deque
from time import perf_counter, time


DEFAULT_SECTION = 'main'
DEFAULT_THRESHOLD_NO_SHOW = 0

MAX_LAPS = 1_000
ZERO_THRESHOLD = 5e-4

OBSOLETE_SECTION_TIME = 3600 # sections older than 1 hour are archived

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
    self.timer_level = None # no actual purpose following addition of graph
    self.sections_last_used = {}
    self.opened_timers = None
    self.timers_graph = None
    self._timer_error = None

    self.reset_timers()
    return

  def _maybe_create_timers_section(self, section=None):
    section = section or DEFAULT_SECTION

    if section in self.timers:
      return

    self.timers[section] = OrderedDict()
    self.timer_level[section] = 0
    self.opened_timers[section] = deque()
    self.timers_graph[section] = OrderedDict()
    self.timers_graph[section]["ROOT"] = {"SLOW" : OrderedDict(), "FAST" : OrderedDict()}
    self._timer_error[section] = False
    return

  def reset_timers(self):
    self.timers = {}
    self.timer_level = {}
    self.opened_timers = {}
    self.timers_graph = {}
    self._timer_error = {}

    self._maybe_create_timers_section()
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
      
      'LAPS' : deque(maxlen=MAX_LAPS),
    }

  def restart_timer(self, sname, section=None):
    section = section or DEFAULT_SECTION
    self.timers[section][sname] = self.get_empty_timer()
    return

  def _add_in_timers_graph(self, sname, section=None):
    section = section or DEFAULT_SECTION
    self.timers[section][sname]['LEVEL'] = self.timer_level[section]
    if sname not in self.timers_graph[section]:
      self.timers_graph[section][sname] = {"SLOW" : OrderedDict(), "FAST" : OrderedDict()}

    self.timers_graph[section][sname]["FAST"] = OrderedDict() ## there is no ordered set, so we use OrderedDict with no values
    return

  def start_timer(self, sname, section=None):
    section = section or DEFAULT_SECTION
    if section == DEFAULT_SECTION:
      assert self.is_main_thread, "Attempted to run threaded timer '{}' without section".format(sname)

    self._maybe_create_timers_section(section)

    if not self.DEBUG:
      return -1

    if sname not in self.timers[section]:
      self.restart_timer(sname, section)

    curr_time = perf_counter()
    self._add_in_timers_graph(sname, section=section)
    self.timers[section][sname]['START'] = curr_time
    self.timers[section][sname]['START_COUNT'] += 1
    if len(self.opened_timers[section]) >= 1:
      parent = self.opened_timers[section][-1]
    else:
      parent = "ROOT"
    #endif

    self.timers_graph[section][parent]["FAST"][sname] = None
    self.timers_graph[section][parent]["SLOW"][sname] = None

    self.timer_level[section] += 1
    self.opened_timers[section].append(sname)

    faulty_timers = self._get_section_faulty_timers(section)
    if len(faulty_timers) > 0 and not self._timer_error[section]:
      self.P("Something is wrong with the timers in section '{}':".format(section), color='r')
      for ft in faulty_timers:
        self.P("  {}: {}".format(ft, self.timers[section][ft]), color='r')
      self._timer_error[section] = True
    #endif

    return curr_time

  def get_time_until_now(self, sname, section=None):
    section = section or DEFAULT_SECTION
    ctimer = self.timers[section][sname]
    return perf_counter() - ctimer['START']

  def get_faulty_timers(self):
    dct_faulty = {}
    for section in self.timers:
      dct_faulty[section] = self._get_section_faulty_timers(section)
    return dct_faulty

  def _get_section_faulty_timers(self, section=None):
    section = section or DEFAULT_SECTION
    lst_faulty = []
    for tmr_name, tmr in self.timers[section].items():
      if (tmr['START_COUNT'] - tmr['STOP_COUNT']) > 1:
        lst_faulty.append(tmr_name)
    return lst_faulty

  def end_timer_no_skip(self, sname, section=None):
    return self.end_timer(sname, skip_first_timing=False, section=section)

  def end_timer(self, sname, skip_first_timing=False, section=None):
    section = section or DEFAULT_SECTION
    if sname not in self.timers[section]:
      return
    result = 0
    self.sections_last_used[section] = time()
    if self.DEBUG:
      self.opened_timers[section].pop()
      self.timer_level[section] -= 1

      ctimer = self.timers[section][sname]
      ctimer['STOP_COUNT'] += 1
      ctimer['END'] = perf_counter()
      result = ctimer['END'] - ctimer['START']
      ctimer['LAPS'].append(result)
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

  def stop_timer(self, sname, skip_first_timing=False, section=None):
    return self.end_timer(sname=sname, skip_first_timing=skip_first_timing, section=section)

  def show_timer_total(self, sname, section=None):
    section = section or DEFAULT_SECTION
    ctimer = self.timers[section][sname]
    cnt = ctimer['COUNT']
    val = ctimer['MEAN'] * cnt
    self.P("  {} = {:.3f} in {} laps".format(sname, val, cnt))
    return

  def _format_timer(self, key, section, was_recently_seen,
                   summary='mean',
                   show_levels=True,
                   show_max=True,
                   show_last=True,
                   show_count=True,
                   div=None,
                   threshold_no_show=None,
                   max_key_size=30,
                   ):

    if threshold_no_show is None:
      threshold_no_show = DEFAULT_THRESHOLD_NO_SHOW

    ctimer = self.timers[section].get(key, None)

    if ctimer is None:
      return

    mean_time = ctimer['MEAN']
    np_laps = np.array(ctimer['LAPS'])
    if len(np_laps) > 0:
      laps_mean = np_laps.mean()
      laps_std = np_laps.std()
      laps_zcount = (np_laps <= ZERO_THRESHOLD).sum()
      laps_nzcount = len(np_laps) - laps_zcount
      laps_nz_mean = np_laps.sum() / laps_nzcount if laps_nzcount > 0 else -1
      laps_low_cnt = (np_laps <= max(ZERO_THRESHOLD, laps_mean - laps_std)).sum()
      laps_low_prc =  laps_low_cnt / np_laps.shape[0] * 100
    else:
      # not mandatory but nice for forever opened 1 time timers
      laps_mean = -1
      laps_std = -1
      laps_zcount = -1
      laps_nzcount = -1
      laps_nz_mean = -1
      laps_low_cnt = -1
      laps_low_prc =  -1
      # end not mandatory

    count = ctimer['COUNT']
    
    if mean_time < threshold_no_show:
      return

    max_time = ctimer['MAX']
    current_time = np_laps[-1] if len(np_laps) > 0 else -1 # ctimer['END'] - ctimer['START']

    if not was_recently_seen:
      key = '[' + key[:max_key_size] + ']'

    if show_levels:
      s_key = '  ' * ctimer['LEVEL'] + key[:max_key_size]
    else:
      s_key = key[:max_key_size]
    msg = None
    if summary in ['mean', 'avg']:
      # self.verbose_log(" {} = {:.4f}s (max lap = {:.4f}s)".format(s_key,mean_time,max_time))
      msg = " {} = {:.4f}s/q:{:.4f}s/nz:{:.4f}s".format(s_key, mean_time, laps_mean, laps_nz_mean)
    else:
      # self.verbose_log(" {} = {:.4f}s (max lap = {:.4f}s)".format(s_key,total, max_time))
      total = mean_time * count
      msg = " {} = {:.4f}s".format(s_key, total)
    if show_max:
      msg += ", max: {:.4f}s".format(max_time)
    if show_last:
      msg += ", lst: {:.4f}s".format(current_time)
    if show_count:
      msg += ", c: {}/L:{:.0f}%".format(count, laps_low_prc)
    if div is not None:
      msg += ", itr(B{}): {:.4f}s".format(div, mean_time / div)
    return msg

  def show_timers(self, **kwargs):
    lst_logs = self.format_timers(**kwargs)
    for l in lst_logs:
      self.verbose_log(l)
    return

  def show_timings(self, **kwargs):
    self.show_timers(**kwargs)
    return

  def format_timers(self, summary=None,
                  title=None,
                  show_levels=True,
                  show_max=True,
                  show_last=True,
                  show_count=True,
                  div=None,
                  threshold_no_show=None,
                  selected_sections=None,
                  ):

    if selected_sections is not None:
      assert isinstance(selected_sections, list)

    if threshold_no_show is None:
      threshold_no_show = DEFAULT_THRESHOLD_NO_SHOW

    if summary is None:
      summary = 'mean'

    if title is None:
      title = ''

    def dfs(visited, graph, node, was_recently_seen, logs, sect):
      if node not in visited:
        formatted_node = self._format_timer(
          key=node,
          section=sect,
          was_recently_seen=was_recently_seen,
          summary=summary,
          show_levels=show_levels, show_last=show_last,
          show_max=show_max, show_count=show_count, div=div,
          threshold_no_show=threshold_no_show
        )
        if formatted_node is not None:
          logs.append(formatted_node)
        visited.add(node)
        slow_keys = list(graph[node]["SLOW"].keys())
        fast_keys = list(graph[node]["FAST"].keys())
        for neighbour in slow_keys:
          recently_seen = neighbour in fast_keys
          dfs(visited, graph, neighbour, recently_seen, logs, sect)
        #endfor
      #endif
    #enddef

    lst_logs = []
    if self.DEBUG:
      if len(title) > 0:
        title = ' ' + title
      header = "Timing results{}:".format(title)
      if threshold_no_show > 0:
        header += " # discarding entries with time < {}".format(threshold_no_show)
      lst_logs.append(header)

      ## SORTING sections and keeping the default section the first one ..
      keys = list(self.timers.keys())
      if selected_sections is not None:
        keys = selected_sections

      add_back_default_section = False
      if DEFAULT_SECTION in keys:
        add_back_default_section = True
        keys.pop(keys.index(DEFAULT_SECTION))
      keys.sort()
      if add_back_default_section:
        keys = [DEFAULT_SECTION] + keys

      old_sections = []
      for section in keys:
        if section in self.sections_last_used and (time() - self.sections_last_used[section]) > OBSOLETE_SECTION_TIME:
          old_sections.append(section)
          continue
        lst_logs.append("Section '{}'".format(section))
        buffer_visited = set()
        dfs(buffer_visited, self.timers_graph[section], "ROOT", True, lst_logs, section)
      if len(old_sections) > 0:
        lst_logs.append("Archived sections older than {:.1f} hrs: {}".format(
          OBSOLETE_SECTION_TIME / 3600, old_sections
        ))
    else:
      self.verbose_log("DEBUG not activated!")
    return lst_logs

  def get_timing_dict(self, skey, section=None):
    section = section or DEFAULT_SECTION
    timers_section = self.timers.get(section, {})
    dct = timers_section.get(skey, {})
    return dct

  def get_timer(self, skey, section=None):
    return self.get_timing_dict(skey, section=section)

  def get_timer_overall_mean(self, skey, section=None):
    tmr = self.get_timer(skey, section=section)
    result = tmr.get('MEAN', 0)
    return result

  def get_timer_mean(self, skey, section=None):
    tmr = self.get_timer(skey, section=section)
    laps = tmr.get('LAPS', [])
    result = np.mean(laps) if len(laps) > 0 else -1
    return result


  def get_timer_count(self, skey, section=None):
    tmr = self.get_timer(skey, section=section)
    result = tmr.get('COUNT', 0)
    return result
  
  def import_timers_section(self, dct_timers, dct_timers_graph, section):
    if section in self.timers:
      self.P("WARNING: Cannot import section '{}' with {} timers as there is already a existing section".format(
        section, len(dct_timers)
      ), color='r')
      return False
    self.timers[section] = dct_timers
    self.timers_graph[section] = dct_timers_graph
    return True
  
  def export_timers_section(self, section):
    if section not in self.timers:
      self.P("WARNING: Cannot export unexisting timers section '{}'".format(
        section
      ), color='r')
      return None, None
    dct_timers = self.timers[section]
    dct_timers_graph = self.timers_graph[section]
    return dct_timers, dct_timers_graph
