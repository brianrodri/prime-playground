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
import time

from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext.webapp import template
import webapp2

import task_entry


class MainPage(webapp2.RequestHandler):
    def get(self):
        urlsafe_cursor = self.request.get('cursor') or None
        cursor = urlsafe_cursor and Cursor(urlsafe=urlsafe_cursor)

        start = time.time()
        open_tasks = (
            task_entry.TaskEntryModel.get_open_tasks('exploration', 'foo'))
        end = time.time()
        open_fetch_duration = end - start

        start = time.time()
        resolved_tasks, cursor_next, has_more_next = (
            task_entry.TaskEntryModel.fetch_history_page(
                'exploration', 'foo', 'resolved', cursor, new_to_old=True))
        _, cursor_prev, has_more_prev = (
            task_entry.TaskEntryModel.fetch_history_page(
                'exploration', 'foo', 'resolved', cursor, new_to_old=False))
        resolved_tasks = list(resolved_tasks)
        end = time.time()
        resolved_fetch_duration = end - start

        template_path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(template_path, {
            'open_tasks': open_tasks,
            'open_tasks_len': len(open_tasks),
            'open_fetch_duration': open_fetch_duration,

            'resolved_tasks': resolved_tasks,
            'resolved_tasks_len': len(resolved_tasks),
            'resolved_fetch_duration': resolved_fetch_duration,

            'next_url': cursor_next and cursor_next.urlsafe(),
            'next_url_visibility': ('visible' if has_more_next else 'hidden'),
            'prev_url': cursor_prev and cursor_prev.urlsafe(),
            'prev_url_visibility': (
                'visible' if cursor and has_more_prev else 'hidden'),
        }))


app = webapp2.WSGIApplication([
    ('/', MainPage),
])
