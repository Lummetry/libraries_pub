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
import sys
import zipfile

class _DownloadMixin(object):
  """
  Mixin for download functionalities that are attached to `libraries.logger.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `libraries.logger.Logger`

  In this mixin we can use any attribute/method of the Logger.
  """

  def __init__(self):
    super(_DownloadMixin, self).__init__()
    return

  def maybe_download_model(self, url, model_file, force_download=False, url_model_cfg=None):
    """
    url11 = 'https://www.dropbox.com/s/t6qfxiopcr8yvlq/60_xomv_employee01_002_e142_acc0.985.pb?dl=1'
    url12 = 'https://www.dropbox.com/s/akzyk9vcuqluzup/60_xomv_employee01_002_e142_acc0.985.pb.txt?dl=1'
    # use maybe_download_model
    log.maybe_download_model(url11, 'model1_dup.pb',
                             force_download=False,
                             url_model_cfg=url12)
    """
    urls = [url]
    fn = [model_file]
    if url_model_cfg is not None:
      urls += [url_model_cfg]
      fn += [model_file + '.txt']

    return self.maybe_download(
      url=urls,
      fn=fn,
      force_download=force_download,
      target='models'
    )

  def maybe_download(self,
                     url,
                     fn=None,
                     force_download=False,
                     target='models',
                     print_progress=True,
                     publish_func=None,
                     publish_only_value=False,
                     verbose=True,
                     unzip=False):
    """
    will (maybe) download a from a given (full) url a file and save to
    target folder in `model_file`.

    The parameter named `publish_func` is a function that publish a message
    through a channel. We do not want to parametrize more than necessary this
    method, so the `publish_func` function should be already charged with
    the channel via a partial.

    The `unzip` parameter comes in when the url(s) is/are zipped folder(s).
    In this case, put `fn` as the name of the local folder, not as the name of the local zip file

    Examples:

    url11 = 'https://www.dropbox.com/s/t6qfxiopcr8yvlq/60_xomv_employee01_002_e142_acc0.985.pb?dl=1'
    fn1 = 'model1.pb'
    url12 = 'https://www.dropbox.com/s/akzyk9vcuqluzup/60_xomv_employee01_002_e142_acc0.985.pb.txt?dl=1'
    fn2 = 'model1.txt'
    url21 = 'https://www.dropbox.com/s/tuywpfzv6ueknj6/70_xfgc03_007_e092_acc0.9413.pb?dl=1'
    fn3 = 'model2.pb'
    url22 = 'https://www.dropbox.com/s/5wrvohffl14qfd3/70_xfgc03_007_e092_acc0.9413.pb.txt?dl=1'
    fn4 = 'model2.txt'
    log = Logger(lib_name='MDL',  config_file='config/duplex_config.txt',  TF_KERAS=False)

    # download two files in output
    log.maybe_download(url=[url11, url12],
                       fn=[fn1,fn2],
                       target='output'
                       )

    # download a txt in data
    log.maybe_download(url=url12,
                       fn='model1_dup.txt',
                       target='data'
                       )

    # download another two files in models with other signature
    log.maybe_download(url={
                        fn3 : url21,
                        fn4 : url22
                        },
                       force_download=True,
                       target='models'
                       )

    # use maybe_download_model
    log.maybe_download_model(url11, 'model1_dup.pb',
                             force_download=False,
                             url_model_cfg=url12)

    """
    import urllib.request
    assert target in ['models', 'data', 'output'], "target must be either 'models', 'data' or 'output'"

    if type(url) is dict:
      urls = [v for k, v in url.items()]
      fns = [k for k in url]
    else:
      if fn is None:
        self.raise_error("fn must be a string or a list if url param does not have file:url dict")
      urls = url
      fns = fn
      if type(urls) is str:
        urls = [urls]
      if type(fns) is str:
        fns = [fns]
      if len(fns) != len(urls):
        self.raise_error("must provided same nr of urls and file names")
    
    if verbose:
      self.P("Checking and (maybe) downloading `{}` file(s) {}".format(
        target, fns))

    def _print_download_progress(count, block_size, total_size):
      """
      Function used for printing the download progress.
      Used as a call-back function in maybe_download_and_extract().
      """

      # Percentage completion.
      pct_complete = float(count * block_size) / total_size

      # Limit it because rounding errors may cause it to exceed 100%.
      pct_complete = min(1.0, pct_complete)

      if publish_func is not None:
        if publish_only_value:
          publish_func(round(pct_complete*100, 2))
        else:
          publish_func("progress:{:.1%}".format(pct_complete))

      if print_progress:
        # Status-message. Note the \r which means the line should overwrite itself.
        msg = "\r- Download progress: {0:.1%}".format(pct_complete)

        # Print it.
        sys.stdout.write(msg)
        sys.stdout.flush()
      return

    # Path for local file.
    download_dir = self.get_target_folder(target=target)

    if download_dir is None:
      self.raise_error("Unknown target {}".format(target))

    saved_files = []
    msgs = []
    for _fn, _url in zip(fns, urls):
      ## useful if _fn is a hierarchy not a filename
      _append_to_download_dir, _fn = os.path.split(_fn)
      _crt_download_dir = os.path.join(download_dir, _append_to_download_dir)
      save_path = os.path.join(_crt_download_dir, _fn)

      # Check if the file already exists, otherwise we need to download it now.
      has_file = os.path.exists(save_path)
      if not has_file or force_download:
        # automatically add .zip in this corner case
        if unzip and not save_path.endswith('.zip'):
          save_path += '.zip'

        # Check if the download directory exists, otherwise create it.
        if not os.path.exists(_crt_download_dir):
          if verbose:
            self.P("Download folder not found - creating")
          os.makedirs(_crt_download_dir)
        if has_file:
          if verbose:
            self.P("Forced download: removing ...{}".format(save_path[-40:]))
          os.remove(save_path)

        # Download the file from the internet.
        if verbose:
          self.P("Downloading {} from {}...".format(_fn, _url[:40]))
        reporthook = _print_download_progress
        file_path, msg = urllib.request.urlretrieve(
          url=_url,
          filename=save_path,
          reporthook=reporthook
        )

        msgs.append(msg)
        print("", flush=True)
        if verbose:
          self.P("Download done and saved in ...{}".format(file_path[-40:]))
        # endif

        if unzip:
          _directory_to_extract_to = os.path.splitext(save_path)[0]
          if verbose:
            self.P("Unzipping '...{}' ...".format(file_path[-40:]))
          if not os.path.exists(_directory_to_extract_to):
            os.makedirs(_directory_to_extract_to)

          with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(_directory_to_extract_to)

          # remove the downloaded zip file as it was already extracted, so it occupies space without any use
          os.remove(file_path)
          saved_files.append(_directory_to_extract_to)
        else:
          saved_files.append(file_path)

      else:
        if verbose:
          self.P("File {} found. Skipping.".format(_fn))
        saved_files.append(save_path)
        msgs.append("'{}' already downloaded.".format(save_path))
    # endfor

    return saved_files, msgs
