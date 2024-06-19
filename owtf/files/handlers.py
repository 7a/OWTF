"""
owtf.files.handlers
~~~~~~~~~~~~~~~~~~~
"""
import datetime
import email.utils
import hashlib
import mimetypes
import os
import stat
import subprocess
import time

import tornado
import tornado.template
import tornado.web
from owtf.api.handlers.base import BaseRequestHandler

__all__ = ["StaticFileHandler", "OutputFileHandler"]


class StaticFileHandler(tornado.web.StaticFileHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "GET,OPTIONS")
        self.set_header("Access-Control-Request-Credentials", "true")
        self.set_header("Access-Control-Allow-Headers", "Authorization,Content-Type")

    def options(self, *args, **kwargs):

        self.set_status(204)
        self.finish()
