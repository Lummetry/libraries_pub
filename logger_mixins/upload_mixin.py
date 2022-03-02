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

import os

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
                     timeout=900,
                     chunk_size=4 * 1024 * 1024,
                     url_type='temporary',
                     progress_fn=None,
                     ):

    """
    Uploads in the folder specific to a dropbox application.

    Steps:
      1. access https://www.dropbox.com/developers/apps
      2. create your app
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

    timeout : int, optional
      Parameter that is passed to the dropbox.Dropbox constructor
      The default is 900.

    chunk_size : int, optional
      Specifies how many bytes are uploaded progressively. If it's None,
      then the whole file is uploaded one time. Very important! If the
      file is big enough and `chunk_size=None` then errors may occur.
      The default is 4*1024*1024

    url_type : str
      Type of url to be generated after the file is uploaded: temporary or shared
    
    progress_fn: callback
      Will be used to report the current progress percent
    
    Returns
    -------
      A downloadable link of the uploaded file

    """
    def _progress(total_size, uploaded_size):
      return round(uploaded_size / total_size * 100, 2)
    
    assert url_type in ['temporary', 'shared']

    import dropbox
    from tqdm import tqdm
    
    uploaded_size = 0
    dbx = dropbox.Dropbox(access_token, timeout=timeout)

    if chunk_size is None:
      with open(file_path, 'rb') as f:
        dbx.files_upload(f.read(), target_path)
    else:
      with open(file_path, "rb") as f:
        file_size = os.path.getsize(file_path)
        if file_size <= chunk_size:
          print(dbx.files_upload(f.read(), target_path))
        else:
          with tqdm(total=file_size, desc="Uploaded") as pbar:
            upload_session_start_result = dbx.files_upload_session_start(
              f.read(chunk_size)
            )
            pbar.update(chunk_size)
            uploaded_size+= chunk_size
            cursor = dropbox.files.UploadSessionCursor(
              session_id=upload_session_start_result.session_id,
              offset=f.tell(),
            )
            commit = dropbox.files.CommitInfo(path=target_path)
            while f.tell() < file_size:
              if (file_size - f.tell()) <= chunk_size:
                print(
                  dbx.files_upload_session_finish(
                    f.read(chunk_size), cursor, commit
                  )
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
              uploaded_size+= chunk_size
              if progress_fn:
                progress_fn(_progress(file_size, uploaded_size))
            # end while
          # end while tqdm
        # endif
      # endwith
    # endif

    url = None
    if url_type == 'temporary':
      url = dbx.files_get_temporary_link(target_path).link
    else:
      url = dbx.sharing_create_shared_link(target_path).url
    return url
  # enddef
