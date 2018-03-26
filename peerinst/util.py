# -*- coding: utf-8 -*-
from __future__ import division, unicode_literals

import itertools

from django.utils.safestring import mark_safe


def get_object_or_none(model_class, *args, **kwargs):
    try:
        return model_class.objects.get(*args, **kwargs)
    except model_class.DoesNotExist:
        return None


def int_or_none(s):
    if s == 'None':
        return None
    return int(s)


def roundrobin(iterables):
    "roundrobin(['ABC', 'D', 'EF']) --> A D E B F C"
    # Recipe taken from the itertools documentation.
    iterables = list(iterables)
    pending = len(iterables)
    nexts = itertools.cycle(iter(it).next for it in iterables)
    while pending:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            pending -= 1
            nexts = itertools.cycle(itertools.islice(nexts, pending))


def make_percent_function(total):
    if total:
        def percent(enum):
            return mark_safe('{:.1f}&nbsp;%'.format(100 * enum / total))
    else:
        def percent(enum):
            return ''
    return percent


class SessionStageData(object):
    """Manages the data to be kept in the session between different question stages."""

    SESSION_KEY = 'dalite_stage_data'

    def __init__(self, session, custom_key):
        self.custom_key = custom_key
        self.session = session
        self.data_dict = session.setdefault(self.SESSION_KEY, {})
        self.data = self.data_dict.get(custom_key)

    def store(self):
        if self.data is None:
            return
        # There is a race condition here:  Django loads the session before calling the view, and
        # stores it after returning.  Two concurrent request can result in changes being lost.
        # This only happens if the same user sends POST requests for two different questions at
        # exactly the same time, which doesn't seem likely (or useful to support).
        self.data_dict[self.custom_key] = self.data
        # Explicitly mark the session as modified since it can't detect nested modifications.
        self.session.modified = True

    def update(self, **kwargs):
        if self.data is None:
            self.data = kwargs
        else:
            self.data.update(**kwargs)

    def get(self, key, default=None):
        if self.data is None:
            return None
        return self.data.get(key, default)

    def clear(self):
        self.data = None
        self.data_dict.pop(self.custom_key, None)
        self.session.modified = True

def load_log_archive(json_log_archive):
    """
    argument:name of json file, which should be in BASE_DIR/log directory, 
    which itself is a list of tuples. Each tuple is of form
           (user_token,[course1,course2,...])

    return: none
    
    usage:
    
    In [1]: from peerinst.util import load_log_archive as load_log_archive
    In [2]: load_log_archive('student-group.json')
    
    """
    import os,json
    from django.contrib.auth.models import User
    from peerinst.models import Student,StudentGroup
    from django.conf import settings
    
    path_to_json = os.path.join(settings.BASE_DIR,'log',json_log_archive)

    with open(path_to_json,'r') as f:
        test=json.load(f)

    new_students = 0 
    new_groups = 0

    for pair in test.items():
        user,created_user = User.objects.get_or_create(username=pair[0])
        if created_user:
            user.save()
            new_students += 1
        student, created_student = Student.objects.get_or_create(student=user)
        if created_student:
            student.save()
        for course in pair[1]:
            group, created_group = StudentGroup.objects.get_or_create(name=course)
            if created_group:
                group.save()
                new_groups += 1
            student.groups.add(group)
            student.save()

    print('{} new students loaded into db'.format(new_students))
    print('{} new groups loaded into db'.format(new_groups))

    return 
