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
import os
import sys
import urllib
import urllib2
import cookielib
import glob

import antd.plugin as plugin

_log = logging.getLogger("antd.strava")

class Strava(plugin.Plugin):

    email = None
    password = None

    logged_in = False
    login_invalid = False

    authenticity_token = None

    def __init__(self):
        import poster.streaminghttp
        cookies = cookielib.CookieJar()
        cookie_handler = urllib2.HTTPCookieProcessor(cookies)
        """
        self.opener = urllib2.build_opener(
                cookie_handler,
                poster.streaminghttp.StreamingHTTPHandler,
                poster.streaminghttp.StreamingHTTPRedirectHandler,
                poster.streaminghttp.StreamingHTTPSHandler)
        """
        self.opener = urllib2.build_opener( cookie_handler )
        # add headers to exactly match firefox
        self.opener.addheaders = [
                ('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:14.0) Gecko/20100101 Firefox/14.0.1'),
                ('Referer', 'http://www.strava.com/login'),
                ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
                ('Accept-Language', 'en-US,en;q=0.8'),
                ('Accept-Encoding', 'gzip, deflate'),
        ]


    def data_available(self, device_sn, format, files):
        if format not in ("tcx"): return files
        result = []
        try:
            for file in files:
                self.login()
                self.upload(format, file)
                result.append(file)
            plugin.publish_data(device_sn, "notif_strava", files)
        except Exception:
            _log.warning("Failed to upload to Strava.", exc_info=True)
        finally:
            return result

    def login(self):
        if self.logged_in: return
        if self.login_invalid: raise InvalidLogin()
        # get session cookies
        _log.debug("Fetching cookies from Strava.")
        resp = self.opener.open("https://www.strava.com/login") # TODO: need to find out how to read the data here
        # Grab the authenticity_token from the Facebook login form
        begin = resp.find('<input name="authenticity_token" type="hidden" value="')
        end = resp.find("\" /></div>\n<div class='facebook'>")
        self.authenticity_token = resp[begin+len('<input name="authenticity_token" type="hidden" value="'):end].strip()
        # build the login string
        login_dict = {
            "utf8": "✓",
            "email": self.email,
            "password": self.password,
            "authenticity_token": self.authenticity_token
        }
        login_str = urllib.urlencode(login_dict)
        # post login credentials
        _log.debug("Posting login credentials to Strava. email=%s", self.email)
        reply = self.opener.open("https://www.strava.com/session", login_str)

        # verify we're logged in - if we're logged in, we'll have "Log Out" at the top of the response page
        _log.debug("Checking if login was successful.")

        if reply.read().find('Log Out') == -1:
            self.login_invalid = True
            raise InvalidLogin()
        else:
            self.logged_in = True

    def upload(self, format, file_name):
        import poster.encode
        with open(file_name) as file:
            upload_dict = {
                "_method": "post",
                "new_uploader": 1,
                "authenticity_token": self.authenticity_token,
                "files": file
            }
            data, headers = poster.encode.multipart_encode(upload_dict)
            _log.info("Uploading %s to Strava.", file_name)
            request = urllib2.Request("http://app.strava.com/upload/files", data, headers)
            self.opener.open(request)