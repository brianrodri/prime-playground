# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
sys.path.append('../oppia_tools/google_appengine_1.9.67/google_appengine')
sys.path.append('../oppia_tools/google-cloud-sdk-251.0.0')

import os
import random
import time
import uuid

from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template
import webapp2

import task_entry


class MainPage(webapp2.RequestHandler):
    def get(self):
        cursor = Cursor(urlsafe=self.request.get('cursor'))

        lo = time.time()
        open_tasks = task_entry.TaskEntryModel.fetch_all_tasks(
            'exploration', 'foo', 'open', reverse=False)
        open_tasks = list(open_tasks)
        hi = time.time()
        open_fetch_duration = hi - lo

        lo = time.time()
        resolved_tasks, next_cursor, more = task_entry.TaskEntryModel.fetch_tasks(
            'exploration', 'foo', 'resolved', cursor, reverse=False)
        _, prev_cursor, prev = task_entry.TaskEntryModel.fetch_tasks(
            'exploration', 'foo', 'resolved', cursor, reverse=True)
        resolved_tasks = list(resolved_tasks)
        hi = time.time()
        resolved_fetch_duration = hi - lo

        template_values = {
            'open_tasks': open_tasks,
            'open_fetch_duration': open_fetch_duration,
            'open_tasks_len': len(open_tasks),
            'resolved_tasks': resolved_tasks,
            'resolved_fetch_duration': resolved_fetch_duration,
            'resolved_tasks_len': len(resolved_tasks),
            'next_url': more and next_cursor.urlsafe(),
            'next_url_style': 'visibility: %s' % (
              'visible' if more and next_cursor else 'hidden'),
            'prev_url': prev and prev_cursor.urlsafe(),
            'prev_url_style': 'visibility: %s' % (
              'visible' if prev and prev_cursor else 'hidden'),
        }
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))


app = webapp2.WSGIApplication([
    ('/', MainPage),
])
