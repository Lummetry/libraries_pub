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

import pyodbc
import pandas as pd

from libraries.db_conn.base import BaseConnector

class ODBCConnector(BaseConnector):
  def __init__(self, **kwargs):
    self._cnxn = None
    self._default_sql_query = "SELECT * FROM {};"
    super(ODBCConnector, self).__init__(**kwargs)
    return

  def _connect(self, **kwargs):
    str_conn = ''
    for k,v in kwargs.items():
      str_conn += '{}={};'.format(k,v)
    self._cnxn = pyodbc.connect(str_conn)
    return

  def _create_reader(self, **kwargs):
    table_data = kwargs['TABLE_DATA']
    chunksize = kwargs.get('CHUNKSIZE', None)
    sql_query = kwargs.get('SQL_QUERY', "")
    if len(sql_query) == 0:
      sql_query = self._default_sql_query.format(table_data)

    if chunksize is None:
      _sql_count_query = "SELECT COUNT(*) FROM {};".format(table_data)
      cursor = self._cnxn.cursor()
      cursor.execute(_sql_count_query)
      nr_rows = cursor.fetchone()[0]
      chunksize = nr_rows
    #endif

    self.reader = pd.read_sql(
      sql=sql_query,
      con=self._cnxn,
      chunksize=chunksize
     )

    return
