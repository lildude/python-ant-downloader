# coding=utf-8
#
# Copyright (c) 2013, Colin Seymour.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   1. Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#   2. Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials
#      provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER AND CONTRIBUTORS
# ''AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY
# WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


import logging
import urllib
import urllib2

import antd.plugin as plugin

_log = logging.getLogger("antd.trainingpeaks")

class TrainingPeaks(plugin.Plugin):

    username = None
    password = None

    def __init__(self):
        self.headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:14.0) Gecko/20100101 Firefox/14.0.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.8',
        }

    def data_available(self, device_sn, format, files):
        if format not in ("tcx"): return files
        result = []
        try:
            for file in files:
                self.upload(format, file)
                result.append(file)
            plugin.publish_data(device_sn, "notif_trainingpeaks", files)
        except Exception:
            _log.warning("Failed to upload to TrainingPeaks.", exc_info=True)
        finally:
            return result

    def upload(self, format, file_name):
        with open(file_name) as file:
            upload_dict = {
                "username": self.username,
                "password": self.password
            }
            auth = urllib.urlencode(upload_dict)
            data = file.read()
            _log.info("Uploading %s to TrainingPeaks.", file_name)
            request = urllib2.Request("https://www.trainingpeaks.com/TPWebServices/EasyFileUpload.ashx?"+auth, data, self.headers)
            resp = urllib2.urlopen(request).read()

            if resp != "OK":
                raise Exception(resp)