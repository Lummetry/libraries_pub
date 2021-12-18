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


def get_api_request_body(request):
  method = request.method
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
  # endif

  if base_params is not None:
    params = dict(base_params)
  else:
    params = {}
  # endif

  return params
