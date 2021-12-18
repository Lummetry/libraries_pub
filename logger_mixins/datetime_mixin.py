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

from datetime import datetime as dt, timedelta
from dateutil.relativedelta import relativedelta

class _DateTimeMixin(object):
  """
  Mixin for date and time functionalities that are attached to `libraries.logger.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `libraries.logger.Logger`

  In this mixin we can use any attribute/method of the Logger.
  """

  def __init__(self):
    super(_DateTimeMixin, self).__init__()
    return

  @staticmethod
  def get_delta_date(date, delta=None, period=None):
    daily_periods = ['d']
    weekly_periods = ['w', 'w-mon', 'w-tue', 'w-wed', 'w-thu', 'w-fri', 'w-sat', 'w-sun']
    monthly_periods = ['m']

    if delta is None:
      delta = 1

    if period is None:
      period = 'd'

    period = period.lower()
    assert period in daily_periods + weekly_periods + monthly_periods

    is_string_date = False
    fmt = '%Y-%m-%d'
    if type(date) is str:
      is_string_date = True
      date = dt.strptime(date, fmt)

    if period in daily_periods:
      delta_date = date + relativedelta(days=delta)
    elif period in monthly_periods:
      delta_date = date + relativedelta(months=delta)
    elif period in weekly_periods:
      delta_date = date + relativedelta(weeks=delta)

    if is_string_date:
      delta_date = dt.strftime(delta_date, fmt)

    return delta_date

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
  def timestamp_begin(ts, begin_of):
    """returns a new timestamp as if it were the start of minute/hour/day/week/month/year"""
    if ts is None:
      ts = dt.now()
    # endif
    if begin_of == 'minute':
      ts = dt(
        year=ts.year, month=ts.month, day=ts.day,
        hour=ts.hour, minute=ts.minute, second=0
      )
    elif begin_of == 'hour':
      ts = dt(
        year=ts.year, month=ts.month, day=ts.day,
        hour=ts.hour, minute=0, second=0
      )
    elif begin_of == 'day':
      ts = dt(
        year=ts.year, month=ts.month, day=ts.day,
        hour=0, minute=0, second=0
      )
    elif begin_of == 'month':
      ts = dt(
        year=ts.year, month=ts.month, day=1,
        hour=0, minute=0, second=0
      )
    elif begin_of == 'year':
      ts = dt(
        year=ts.year, month=1, day=1,
        hour=0, minute=0, second=0
      )
    # endif
    return ts
