# coding: utf-8
#
# Copyright 2020 The Oppia Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Models related to Oppia improvement tasks."""

from __future__ import absolute_import
from __future__ import unicode_literals

import datetime

import random
import uuid

from google.appengine.ext import ndb
from google.appengine.ext.ndb import metadata

TEST_ONLY_ENTITY_TYPE = 'TEST_ONLY_ENTITY_TYPE'
ENTITY_TYPE_EXPLORATION = 'exploration'
ENTITY_TYPES = (
    TEST_ONLY_ENTITY_TYPE,
    ENTITY_TYPE_EXPLORATION,
)

STATUS_OPEN = 'open'
STATUS_DEPRECATED = 'deprecated'
STATUS_RESOLVED = 'resolved'
STATUS_CHOICES = (
    STATUS_OPEN,
    STATUS_DEPRECATED,
    STATUS_RESOLVED,
)

TEST_ONLY_TARGET_TYPE = 'TEST_ONLY_TARGET_TYPE'
TARGET_TYPE_STATE = 'state'
TARGET_TYPES = (
    TEST_ONLY_TARGET_TYPE,
    TARGET_TYPE_STATE,
)

TASK_TYPES = (
    'needs-guiding-responses',
    'successive-incorrect-answers',
    'high-bounce-rate',
    'ineffective-feedback-loop',
)

ENTITY_TYPE_TARGETS = {
    ENTITY_TYPE_EXPLORATION: {
        TARGET_TYPE_STATE,
    }
}


class TaskEntryModel(ndb.Model):
    """Task entry corresponding to an actionable task in the improvements tab.

    Instances of a class have an ID with the form:
        [entity_type].[entity_id].[task_type].[uuid]
    """

    # When this entity was first created. This can be overwritten and
    # set explicitly.
    created_on = ndb.DateTimeProperty(indexed=True, required=True)
    # When this entity was last updated. This cannot be set directly.
    last_updated = ndb.DateTimeProperty(indexed=True, required=True)
    # Whether the current version of the model instance is deleted.
    deleted = ndb.BooleanProperty(indexed=True, default=False)

    # The type of entity a task entry refers to.
    entity_type = ndb.StringProperty(
        required=True, indexed=True, choices=ENTITY_TYPES)
    # The ID of the entity a task entry refers to.
    entity_id = ndb.StringProperty(
        required=True, indexed=True)
    # The version of the entity a task entry refers to.
    entity_version = ndb.IntegerProperty(
        required=True, indexed=True)
    # The type of task a task entry tracks.
    task_type = ndb.StringProperty(
        required=True, indexed=True, choices=TASK_TYPES)
    # The type of sub-entity a task entry focuses on.
    target_type = ndb.StringProperty(
        default=None, required=False, indexed=True, choices=TARGET_TYPES)
    # Uniquely identifies the sub-entity a task entry focuses on.
    target_id = ndb.StringProperty(
        default=None, required=False, indexed=True)

    # Tracks the state/progress of a task entry.
    status = ndb.StringProperty(
        required=True, indexed=True, choices=STATUS_CHOICES)
    # ID of the user who closed the task, if any.
    closed_by = ndb.StringProperty(
        default=None, required=False, indexed=True)
    # The date and time at which a task was closed or deprecated.
    closed_on = ndb.DateTimeProperty(
        default=None, required=False, indexed=True)
    # Auto-generated string which provides a one-line summary of the task.
    issue_description = ndb.StringProperty(
        default=None, required=False, indexed=False)

    @property
    def id(self):
        """A unique id for this model instance."""
        return self.key.id()

    @classmethod
    def get(cls, entity_id, strict=True):
        """Gets an entity by id.

        Args:
            entity_id: str.
            strict: bool. Whether to fail noisily if no entity with the given id
                exists in the datastore. Default is True.

        Returns:
            None, if strict == False and no undeleted entity with the given id
            exists in the datastore. Otherwise, the entity instance that
            corresponds to the given id.

        Raises:
            Exception: if strict == True and no undeleted entity with the given
                id exists in the datastore.
        """
        entity = cls.get_by_id(entity_id)
        if entity and entity.deleted:
            entity = None

        if strict and entity is None:
            raise Exception(
                'Entity for class %s with id %s not found' %
                (cls.__name__, entity_id))
        return entity

    @classmethod
    def get_multi(cls, entity_ids, include_deleted=False):
        """Gets list of entities by list of ids.

        Args:
            entity_ids: list(str).
            include_deleted: bool. Whether to include deleted entities in the
                return list. Default is False.

        Returns:
            list(*|None). A list that contains model instances that match
            the corresponding entity_ids in the input list. If an instance is
            not found, or it has been deleted and include_deleted is False,
            then the corresponding entry is None.
        """
        entity_keys = []
        none_argument_indices = []
        for index, entity_id in enumerate(entity_ids):
            if entity_id:
                entity_keys.append(ndb.Key(cls, entity_id))
            else:
                none_argument_indices.append(index)

        entities = ndb.get_multi(entity_keys)
        for index in none_argument_indices:
            entities.insert(index, None)

        if not include_deleted:
            for i in python_utils.RANGE(len(entities)):
                if entities[i] and entities[i].deleted:
                    entities[i] = None
        return entities

    def put(self, update_last_updated_time=True):
        """Stores the given ndb.Model instance to the datastore.

        Args:
            update_last_updated_time: bool. Whether to update the
                last_updated_field of the model.

        Returns:
            Model. The entity that was stored.
        """
        if self.created_on is None:
            self.created_on = datetime.datetime.utcnow()

        if update_last_updated_time or self.last_updated is None:
            self.last_updated = datetime.datetime.utcnow()

        return super(TaskEntryModel, self).put()

    @classmethod
    def put_multi(cls, entities, update_last_updated_time=True):
        """Stores the given ndb.Model instances.

        Args:
            entities: list(ndb.Model).
            update_last_updated_time: bool. Whether to update the
                last_updated_field of the entities.
        """
        for entity in entities:
            if entity.created_on is None:
                entity.created_on = datetime.datetime.utcnow()

            if update_last_updated_time or entity.last_updated is None:
                entity.last_updated = datetime.datetime.utcnow()

        ndb.put_multi(entities)

    @classmethod
    def delete_multi(cls, entities):
        """Deletes the given ndb.Model instances.

        Args:
            entities: list(ndb.Model).
        """
        keys = [entity.key for entity in entities]
        ndb.delete_multi(keys)

    @classmethod
    def delete_by_id(cls, instance_id):
        """Deletes instance by id.

        Args:
            instance_id: str. Id of the model to delete.
        """
        ndb.Key(cls, instance_id).delete()

    def delete(self):
        """Deletes this instance."""
        super(TaskEntryModel, self).key.delete()

    @classmethod
    def get_all(cls, include_deleted=False):
        """Gets iterable of all entities of this class.

        Args:
            include_deleted: bool. If True, then entities that have been marked
                deleted are returned as well. Defaults to False.

        Returns:
            iterable. Filterable iterable of all entities of this class.
        """
        query = cls.query()
        if not include_deleted:
            query = query.filter(cls.deleted == False)  # pylint: disable=singleton-comparison
        return query

    @classmethod
    def get_new_id(cls, entity_name):
        """Gets a new id for an entity, based on its name.

        The returned id is guaranteed to be unique among all instances of this
        entity.

        Args:
            entity_name: The name of the entity. Coerced to a utf-8 encoded
                string. Defaults to ''.

        Returns:
            str. New unique id for this entity class.

        Raises:
            Exception: An ID cannot be generated within a reasonable number
                of attempts.
        """
        for _ in python_utils.RANGE(MAX_RETRIES):
            new_id = utils.convert_to_hash(
                '%s%s' % (entity_name, utils.get_random_int(RAND_RANGE)),
                ID_LENGTH)
            if not cls.get_by_id(new_id):
                return new_id

        raise Exception('New id generator is producing too many collisions.')

    @classmethod
    def fetch_open_tasks(cls, entity_type, entity_id):
        return list(cls.query(
            cls.entity_type == entity_type,
            cls.entity_id == entity_id,
            cls.status == STATUS_OPEN))

    @classmethod
    def get_history_page(
            cls, entity_type, entity_id, status, cursor, new_to_old=False):
        return (
            cls.query(
                cls.entity_type == entity_type,
                cls.entity_id == entity_id,
                cls.status == status)
            .order(-cls.last_updated if new_to_old else cls.last_updated)
            .fetch_page(10, start_cursor=cursor))

    @classmethod
    def get_task_id(
            cls, entity_type, entity_id, entity_version, task_type,
            target_type, target_id):
        """Generates a new task entry ID.

        Args:
            entity_type: str. The type of entity a task entry refers to.
            entity_id: str. The ID of the entity a task entry refers to.
            task_type: str. The type of task a task entry tracks.

        Returns:
            str. An ID available for use for a new task entry.
        """
        return '.'.join(str(piece) for piece in (
            entity_type, entity_id, entity_version, task_type,
            target_type, target_id))


def get_random_task(entity_id=None):
    entity_type = 'exploration'
    entity_id = entity_id or uuid.uuid4().hex
    entity_version = 1
    task_type = random.choice(TASK_TYPES)
    target_type = random.choice(TARGET_TYPES)
    target_id = uuid.uuid4().hex
    status = random.choice(STATUS_CHOICES)
    issue_description = uuid.uuid4().hex
    return TaskEntryModel(
        id=TaskEntryModel.get_task_id(
            entity_type, entity_id, entity_version, task_type,
            target_type, target_id),
        entity_type=entity_type,
        entity_id=entity_id,
        entity_version=entity_version,
        task_type=task_type,
        target_type=target_type,
        target_id=target_id,
        status=status,
        issue_description=issue_description)
