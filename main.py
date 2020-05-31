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
import re
import time

from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext.webapp import template
import webapp2

import task_entry
import task_entry_with_computed_property
import task_entry_with_real_property


class PageBase(webapp2.RequestHandler):
    def get(self):
        urlsafe_cursor = self.request.get('cursor') or None
        cursor = urlsafe_cursor and Cursor(urlsafe=urlsafe_cursor)

        start = time.time()
        open_tasks = (
            self.TASK_MODEL.get_open_tasks('exploration', 'foo', 1))
        end = time.time()
        open_fetch_duration = end - start

        start = time.time()
        resolved_tasks, cursor_next, has_more_next = (
            self.TASK_MODEL.fetch_history_page(
                'exploration', 'foo', 1, cursor, new_to_old=True))
        _, cursor_prev, has_more_prev = (
            self.TASK_MODEL.fetch_history_page(
                'exploration', 'foo', 1, cursor, new_to_old=False))
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


class GeneratePageBase(webapp2.RequestHandler):
    BATCH_SIZE = 1000
    def get(self):
        self.response.content_type = 'text/plain'
        num = self.request.get('num')
        task_id = self.request.get('task_id') or None

        num_remaining = int(num or 0)
        num_todo = min(num_remaining, self.BATCH_SIZE * 4)
        while num_todo:
            batch_size = min(num_todo, self.BATCH_SIZE)
            self.TASK_MODEL.put_multi(
                [self.TASK_MODEL.get_random_task(task_id) for _ in range(batch_size)])
            self.response.out.write('%d entities written\n' % batch_size)
            num_todo -= batch_size
            num_remaining -= batch_size

        if num_remaining:
            next_run_path = (
                re.sub('num\=\d+', 'num=%d' % num_remaining, self.request.path_qs))
            self.redirect(next_run_path)
        else:
            self.response.out.write('done')


class TaskPage(PageBase):
    TASK_MODEL = task_entry.TaskEntryModel
class GenerateTaskPage(GeneratePageBase):
    TASK_MODEL = task_entry.TaskEntryModel


class TaskWithComputedPropertyPage(PageBase):
    TASK_MODEL = task_entry_with_computed_property.TaskEntryWithComputedPropertyModel
class GenerateTaskWithComputedPropertyPage(GeneratePageBase):
    TASK_MODEL = task_entry_with_computed_property.TaskEntryWithComputedPropertyModel


class TaskWithRealPropertyPage(PageBase):
    TASK_MODEL = task_entry_with_real_property.TaskEntryWithRealPropertyModel
class GenerateTaskWithRealPropertyPage(GeneratePageBase):
    TASK_MODEL = task_entry_with_real_property.TaskEntryWithRealPropertyModel


app = webapp2.WSGIApplication([
    ('/', TaskPage),
    ('/base', TaskPage),
    ('/base/new', GenerateTaskPage),
    ('/real', TaskWithRealPropertyPage),
    ('/real/new', GenerateTaskWithRealPropertyPage),
    ('/comp', TaskWithComputedPropertyPage),
    ('/comp/new', GenerateTaskWithComputedPropertyPage),
])
