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


    Notes: 
    The argument to this function is made using the following offline code 
    (Ideally this function should work directly from log files, TO DO):

    fname = 'data_mydalite/studentlog1.log'
    logs=[]
    for line in open(fname,'r'):
        logs.append(json.loads(line))
    
    fname = 'data_mydalite/studentlog2.log'
    for line in open(fname,'r'):
        logs.append(json.loads(line))    
    
    students={}
    for l in logs:
        # if we have seen this student before:
        if l['username'] in students:
            # if this student has not been assigned to this group
            if l['course_id'] not in students[l['username']]:
                students[l['username']].append(l['course_id'])
        else:
            students[l['username']]=[]
            students[l['username']].append(l['course_id'])

    fname = 'student-group.json'
    with open(fname,'w') as f:
        json.dump(students,f)

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


def load_timestamps_from_logs(log_filename_list):
    """
    function to parse log files and add timestamps to previous records in Answer model with newly added time field
    argument: list of filenames in log directory
    return: none

    usage from shell: 
    In [1]: from peerinst.util import load_timestamps_from_logs  
    In [2]: load_timestamps_from_logs(['student.log','student2.log'])    

    """
    import os,json
    from django.utils import dateparse,timezone
    from peerinst.models import Answer
    from django.conf import settings


    # load logs
    logs = []
    for name in log_filename_list:
        fname = os.path.join(settings.BASE_DIR,'log',name)
        for line in open(fname,'r'):
            log_event = json.loads(line)
            if log_event['event_type']=='save_problem_success':
                logs.append(log_event)
    print('{} save_problem_success log events'.format(len(logs)))

    # get records that don't have a timestamp
    answer_qs = Answer.objects.filter(time__isnull=True)

    records_updated = 0
    records_not_in_logs = 0

    # iterate through each record, find its log entry, and save the timestamp
    print('{} records to parse'.format(len(answer_qs)))
    print('start time: {}'.format(timezone.now()))
    records_parsed = 0
    for a in answer_qs:
        for log in logs:
            if (log['username']==a.user_token) and (log['event']['assignment_id']==a.assignment_id) and (log['event']['question_id']==a.question_id):
                timestamp = timezone.make_aware(dateparse.parse_datetime(log['time']))
                a.time = timestamp
                a.save()
                records_updated += 1
        if a.time is None:
            records_not_in_logs += 1
        records_parsed +=1
        if records_parsed % 1000==0:
            print('{} db records parsed'.format(records_parsed))
            print('{} db records updated'.format(records_updated))
            print('time: {}'.format(timezone.now()))

    print('End time: {}'.format(timezone.now()))
    print('{} total answer table records in db updated with time field from logs'.format(records_updated))
    print('{} total answer table records in db not found in logs; likely seed rationales from teacher backend'.format(records_updated))
    return
