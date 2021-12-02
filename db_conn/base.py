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


from libraries import LummetryObject
import abc
import time as tm

class BaseConnector(LummetryObject):
  def __init__(self, log, config, **kwargs):
    self.reader = None
    self.config = config
    super(BaseConnector, self).__init__(log=log, prefix_log='[CONN]', **kwargs)
    return

  def connect(self, nr_retries=None):
    if nr_retries is None:
      nr_retries = 5

    self.P("Connecting ...")
    count = 0
    while count < nr_retries:
      count += 1
      try:
        self._connect(**self.config['CONNECT_PARAMS'])
        self.P("connection created.", color='g')
        break
      except Exception as err:
        self.P("ERROR! connection failed\n{}".format(err))
        tm.sleep(0.5)
      #end try-except
    #endwhile
    return

  def data_chunk_generator(self):
    if not self.reader:
      self._create_reader(**self.config['QUERY_PARAMS'])

    self.P("Iterating chunks ...", color='b')
    for i,df_chunk in enumerate(self.reader):
      d1, d2 = df_chunk.shape
      print_msg = "Chunk events: {}".format(d1)
      if i == 0:
        print_msg += " / cols: {}".format(d2)

      self.P(print_msg, color='b')

      yield df_chunk


  def _connect(self, **kwargs):
    return

  @abc.abstractmethod
  def _create_reader(self, **kwargs):
    raise NotImplementedError
