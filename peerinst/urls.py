# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import include, url
from django.contrib.auth.views import login

from . import admin_views
from . import views

urlpatterns = [
    url(r'^$', views.AssignmentListView.as_view(), name='assignment-list'),
    url(r'^assignment/(?P<assignment_id>[^/]+)/', include([
        url(r'^$', views.QuestionListView.as_view(), name='question-list'),
        url(r'(?P<question_id>\d+)/', include([
            url(r'^$', views.question, name='question'),
            url(r'^reset/$', views.reset_question, name='reset-question'),
        ])),
    ])),
    url(r'^heartbeat/$', views.HeartBeatUrl.as_view(), name='heartbeat'),
    url(r'^admin/$', admin_views.AdminIndexView.as_view(), name='admin-index'),
    url(r'^admin/peerinst/', include([
        url(r'^assignment_results/(?P<assignment_id>[^/]+)/', include([
            url(r'^$', admin_views.AssignmentResultsView.as_view(), name='assignment-results'),
            url(r'^rationales/(?P<question_id>\d+)$', admin_views.QuestionRationaleView.as_view(), name='question-rationales'),
        ])),
        url(r'^question_preview/(?P<question_id>[^/]+)$',
            admin_views.QuestionPreviewView.as_view(), name='question-preview'),
        url(r'^fake_usernames/$', admin_views.FakeUsernames.as_view(), name='fake-usernames'),
        url(r'^fake_countries/$', admin_views.FakeCountries.as_view(), name='fake-countries'),
        url(r'^attribution_analysis/$', admin_views.AttributionAnalysis.as_view(),
            name='attribution-analysis'),
    ])),
    url(r'^teacher-account/(?P<pk>[0-9]+)/$', views.TeacherDetailView.as_view(), name='teacher'),
    url(r'^teacher/(?P<pk>[0-9]+)/$', views.TeacherUpdate.as_view(), name='teacher-update'),
    url(r'^teacher/(?P<pk>[0-9]+)/assignments/$', views.TeacherAssignments.as_view(), name='teacher-assignments'),
    url(r'^teacher/(?P<pk>[0-9]+)/assignments/modify/$', views.modify_assignment, name='modify-teacher-assignments'),

    url(r'^teacher/(?P<pk>[0-9]+)/blinks/$', views.TeacherBlinks.as_view(), name='teacher-blinks'),



    url(r'^teacher/(?P<pk>[0-9]+)/groups/$', views.TeacherGroups.as_view(), name='teacher-groups'),
    url(r'^teacher/(?P<pk>[0-9]+)/groups/modify/$', views.modify_group, name='modify-teacher-groups'),
    url(r'^login/$', login, name='login'),
    url(r'^welcome/$', views.welcome, name='welcome'),
    url(r'^logout/$', views.logout_view, name='logout'),

    
    # testing
    url(r'^blink/(?P<pk>[0-9]+)/$', views.BlinkQuestionFormView.as_view(), name='blink-question'),
    url(r'^blink/(?P<pk>[0-9]+)/summary/$', views.BlinkQuestionDetailView.as_view(), name='blink-summary'),
    url(r'^blink/(?P<pk>[0-9]+)/count/$', views.blink_count, name='blink-count'),
    url(r'^blink/(?P<pk>[0-9]+)/close/$', views.blink_close, name='blink-close'),
    url(r'^blink/(?P<pk>[0-9]+)/latest_results/$', views.blink_latest_results, name='blink-results'),
    url(r'^blink/(?P<pk>[0-9]+)/reset/$', views.blink_reset, name='blink-reset'),
    url(r'^blink/(?P<pk>[0-9]+)/status/$', views.blink_status, name='blink-status'),
    url(r'^blink/(?P<pk>[0-9]+)/set_current/$', views.blink_set_current, name='blink-set-current'),
]
