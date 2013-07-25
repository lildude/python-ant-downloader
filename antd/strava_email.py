# Copyright (c) 2013, Colin Seymour
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
import os
import sys
import urllib
import urllib2
import cookielib
import json
import glob

import antd.plugin as plugin

_log = logging.getLogger("antd.connect")

class StravaEmail(plugin.Plugin):

    server = None
    smtp_server = None
    smtp_port = None
    smtp_username = None
    smtp_password = None

    logged_in = False

    def __init__(self):
        from smtplib import SMTP
        self.server = SMTP()
        pass

    def data_available(self, device_sn, format, files):
        if format not in ("tcx"): return files
        result = []
        try:
            for file in files:
                self.login()
                self.upload(format, file)
                result.append(file)
            self.logout()
        except Exception:
            _log.warning("Failed to upload to Strava.", exc_info=True)
        finally:
            return result

    def logout(self):
        self.server.close()

    def login(self):
        if self.logged_in: return
        self.server.connect(self.smtp_server, self.smtp_port)
        self.server.ehlo()
        if self.smtp_password:
            self.server.starttls()
            self.server.ehlo()
            self.server.login(self.smtp_username, self.smtp_password)
        self.logged_in = True
    
    def upload(self, format, file_name):
        from email.mime.base import MIMEBase
        from email.mime.multipart import MIMEMultipart
        import datetime
        from email import encoders
        outer = MIMEMultipart()
        outer['Subject'] = 'Garmin Data Upload from %s' % datetime.date.today()
        outer['To' ] = 'upload@strava.com'
        outer['From' ] = self.smtp_username
        outer.preamble = 'You will not see this in a MIME-aware mail reader.\n'
        with open(file_name, 'rb') as fp:
            msg = MIMEBase('application', 'octet-stream')
            msg.set_payload(fp.read())
        encoders.encode_base64(msg)
        msg.add_header('Content-Disposition', 'attachment', filename=file_name)
        outer.attach(msg)
        self.server.sendmail(self.smtp_username, 'upload@strava.com', outer.as_string())

class InvalidLogin(Exception): pass


# vim: ts=4 sts=4 et
