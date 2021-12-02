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
@author: Lummetry.AI
@project: 
@description:
"""

import os
import requests
import json


def dbx_get_team_member_id(access_token, email):
  headers = {
    'Content-Type': 'application/json',
    "Authorization": "Bearer {}".format(access_token)
  }

  resp = requests.post(
    'https://api.dropboxapi.com/2/team/members/list_v2',
    headers=headers,
    data=json.dumps({"limit": 100, "include_removed": False})
  )
  members = resp.json()['members']
  team_member_id = None
  for member in members:
    if member['profile']['email'] == email:
      team_member_id = member['profile']['team_member_id']
      break
  # endfor
  return team_member_id

def dbx_make_folder_shareable(access_token, path_folder, team_member_id):
  headers = {
    'Content-Type': 'application/json',
    "Authorization": "Bearer {}".format(access_token),
    'Dropbox-API-Select-User': team_member_id
  }

  data = {
    "path": path_folder,
    "acl_update_policy": "editors",
    "force_async": False,
    "member_policy": "team",
    "shared_link_policy": "members",
    "access_inheritance": "inherit"
  }

  resp = requests.post(
    "https://api.dropboxapi.com/2/sharing/share_folder",
    headers=headers,
    data=json.dumps(data)
  )

  try:
    shared_folder_id = resp.json()['shared_folder_id']
  except:
    shared_folder_id = None

  return shared_folder_id

def dbx_share_folder(access_token, shared_folder_id, team_member_id, lst_team_members):
  if not shared_folder_id:
    return

  headers = {
    'Content-Type': 'application/json',
    "Authorization": "Bearer {}".format(access_token),
    'Dropbox-API-Select-User': team_member_id
  }

  data = {
    'shared_folder_id': shared_folder_id,
    'members': [],
    'quiet': True,
  }
  for team_member in lst_team_members:
    data['members'].append(
      {"member": {".tag": "email", "email": team_member}, "access_level": "editor"}
    )
  # endfor

  resp = requests.post(
    'https://api.dropboxapi.com/2/sharing/add_folder_member',
    headers=headers,
    data=json.dumps(data)
  )

  return


class _UploadMixin(object):
  """
  Mixin for upload functionalities that are attached to `libraries.logger.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `libraries.logger.Logger`

  In this mixin we can use any attribute/method of the Logger.
  """

  def __init__(self):
    super(_UploadMixin, self).__init__()
    return

  @staticmethod
  def dropbox_upload(access_token,
                     file_path,
                     target_path,
                     team_dbx=False,
                     email=None,
                     timeout=None,
                     chunk_size=None,
                     url_type=None):

    """
    Uploads in the folder specific to a dropbox application.

    Steps:
      1. access https://www.dropbox.com/developers/apps
      2. create your app (could be personal app or team app)
      3. generate an unlimited access token

    Parameters
    ----------

    access_token : str
      The token generated in the dropbox app @ step 3

    file_path : str
      Path to the local file that needs to be uploaded in dropbox

    target_path : str
      Path to the remote dropbox path. Very important! This should start
      with '/' (e.g. '/DATA/file.txt')

    team_dbx : boolean, optional
      Specifies whether the access token is for a team application or for a personal application
      Default is False

    email : str, optional
      User dropbox email.
      This parameter is taken into consideration when `team_dbx=True`. It is mandatory in this case because
      you can upload files using a team access token just when you specify who you are (which is your dropbox account)
      The default is None ('laurentiu@lummetry.ai')

    timeout : int, optional
      Parameter that is passed to the dropbox.Dropbox constructor
      The default is None (900).

    chunk_size : int, optional
      Specifies how many bytes are uploaded progressively. If it's None,
      then the whole file is uploaded one time. Very important! If the
      file is big enough and `chunk_size=None` then errors may occur.
      The default is None (4*1024*1024)

    url_type : str, optional
      Type of url to be generated after the file is uploaded: temporary or shared
      The default is None ('temporary')

    Returns
    -------
      A downloadable link of the uploaded file

    """
    lst_team_members = [
      'razvan.ciobanu@lummetry.ai',
      'alexandru.purdila@lummetry.ai',
      'andrei@lummetry.ai',
      'mihai.constantinescu@lummetry.ai',
      'laurentiu@lummetry.ai',
    ]

    if timeout is None:
      timeout = 900

    if chunk_size is None:
      chunk_size = 4*1024*1024

    if url_type is None:
      url_type = 'temporary'

    assert url_type in ['temporary', 'shared']

    import dropbox
    from tqdm import tqdm

    if not team_dbx:
      dbx = dropbox.Dropbox(access_token, timeout=timeout)
    else:
      if email is None:
        email = 'laurentiu@lummetry.ai'

      team_member_id = dbx_get_team_member_id(access_token=access_token, email=email)
      if team_member_id is None:
        return

      dbx = dropbox.DropboxTeam(access_token, timeout=timeout).as_user(team_member_id)
    #endif

    if chunk_size is None:
      with open(file_path, 'rb') as f:
        dbx.files_upload(f.read(), target_path)
    else:
      with open(file_path, "rb") as f:
        file_size = os.path.getsize(file_path)
        if file_size <= chunk_size:
          response = dbx.files_upload(f.read(), target_path)
        else:
          with tqdm(total=file_size, desc="Uploaded") as pbar:
            upload_session_start_result = dbx.files_upload_session_start(
              f.read(chunk_size)
            )
            pbar.update(chunk_size)
            cursor = dropbox.files.UploadSessionCursor(
              session_id=upload_session_start_result.session_id,
              offset=f.tell(),
            )
            commit = dropbox.files.CommitInfo(path=target_path)
            while f.tell() < file_size:
              if (file_size - f.tell()) <= chunk_size:
                response = dbx.files_upload_session_finish(
                  f.read(chunk_size), cursor, commit
                )
              else:
                dbx.files_upload_session_append(
                  f.read(chunk_size),
                  cursor.session_id,
                  cursor.offset,
                )
                cursor.offset = f.tell()
              # endif
              pbar.update(chunk_size)
            # end while
          # end while tqdm
        # endif
      # endwith
    # endif

    if url_type == 'temporary':
      url = dbx.files_get_temporary_link(target_path).link
    else:
      f = dbx.sharing_create_shared_link(target_path)
      url = f.url

    if team_dbx:
      shared_folder_id = dbx_make_folder_shareable(
        access_token=access_token,
        path_folder='/'.join(target_path.split('/')[:2]),
        team_member_id=team_member_id
      )

      dbx_share_folder(
        access_token=access_token,
        shared_folder_id=shared_folder_id,
        team_member_id=team_member_id,
        lst_team_members=lst_team_members,
      )
    #endif

    return url
  # enddef
