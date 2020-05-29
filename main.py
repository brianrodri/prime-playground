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
        cursor = Cursor(urlsafe=self.request.get('cursor'))

        lo = time.time()
        tasks, next_cursor, more = task_entry.TaskEntryModel.fetch_open_tasks(
            'exploration', 'foo', cursor, reverse=False)
        _, prev_cursor, prev = task_entry.TaskEntryModel.fetch_open_tasks(
            'exploration', 'foo', cursor, reverse=True)
        hi = time.time()

        template_values = { 'tasks': tasks }

        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))
        self.response.out.write('<div>Done in %s msec</div>' % str(hi - lo))

        if prev and prev_cursor:
            self.response.out.write('<a href="/?cursor=%s">&lt;- Prev</a>' %
                                    prev_cursor.urlsafe())
        if more and next_cursor:
            self.response.out.write('<a href="/?cursor=%s">Next -&gt;</a>' %
                                    next_cursor.urlsafe())


app = webapp2.WSGIApplication([
    ('/', MainPage),
])
