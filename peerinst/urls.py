# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import include, url
from django.contrib.auth.views import login,password_reset,password_reset_done,password_reset_confirm,password_reset_complete

#testing
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.cache import cache_page

from . import admin_views
from . import views

urlpatterns = [
    # DALITE
    # Assignment table of contents - Enforce sameorigin to prevent access from LMS
    url(r'^$', xframe_options_sameorigin(views.AssignmentListView.as_view()), name='assignment-list'),
    url(r'^assignment/(?P<assignment_id>[^/]+)/', include([\
        # Question table of contents for assignment - Enforce sameorigin to prevent access from LMS
        url(r'^$', xframe_options_sameorigin(views.QuestionListView.as_view()), name='question-list'),\
        url(r'(?P<question_id>\d+)/', include([\
            # Dalite question
            url(r'^$', views.question, name='question'),\
            # Question reset (for testing purposes) - Enforce sameorigin to prevent access from LMS
            url(r'^reset/$', views.reset_question, name='reset-question'),
        ])),
        url(r'^update/$',views.AssignmentUpdateView.as_view(),name='assignment-update')
    ])),
    url(r'^heartbeat/$', views.HeartBeatUrl.as_view(), name='heartbeat'),

    # Admin
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

    # Teachers
    url(r'^teacher-account/(?P<pk>[0-9]+)/$', views.TeacherDetailView.as_view(), name='teacher'),
    url(r'^teacher/(?P<pk>[0-9]+)/$', views.TeacherUpdate.as_view(), name='teacher-update'),
    url(r'^teacher/(?P<pk>[0-9]+)/assignments/$', views.TeacherAssignments.as_view(), name='teacher-assignments'),
    url(r'^teacher/(?P<pk>[0-9]+)/blinks/$', views.TeacherBlinks.as_view(), name='teacher-blinks'),
    url(r'^teacher/(?P<pk>[0-9]+)/groups/$', views.TeacherGroups.as_view(), name='teacher-groups'),

    # Auth
    url(r'^landing_page/$', views.landing_page, name='landing_page'),
    url(r'^login/$', login, name='login'),
    url(r'^password_reset/$', password_reset, name='password_reset'),
    url(r'^password_reset_done/$', password_reset_done, name='password_reset_done'),
    url(r'^password_reset_confirm/$', password_reset_confirm, name='password_reset_confirm'),
    url(r'^password_reset_complete/$', password_reset_complete, name='password_reset_complete'),
    url(r'^welcome/$', views.welcome, name='welcome'),
    url(r'^logout/$', views.logout_view, name='logout'),
    url(r'^access_denied/$', views.access_denied, name='access_denied'),

    # Blink
    url(r'^blink/(?P<pk>[0-9]+)/$', views.BlinkQuestionFormView.as_view(), name='blink-question'),
    url(r'^blink/(?P<pk>[0-9]+)/summary/$', views.BlinkQuestionDetailView.as_view(), name='blink-summary'),
    url(r'^blink/(?P<pk>[0-9]+)/count/$', views.blink_count, name='blink-count'),
    url(r'^blink/(?P<pk>[0-9]+)/close/$', views.blink_close, name='blink-close'),
    url(r'^blink/(?P<pk>[0-9]+)/latest_results/$', views.blink_latest_results, name='blink-results'),
    url(r'^blink/(?P<pk>[0-9]+)/reset/$', views.blink_reset, name='blink-reset'),
    url(r'^blink/(?P<pk>[0-9]+)/status/$', views.blink_status, name='blink-status'),
    url(r'^blink/(?P<username>\w+)/$', views.blink_get_current, name='blink-get-current'),
    url(r'^blink/(?P<username>\w+)/url/$', cache_page(1)(views.blink_get_current_url), name='blink-get-current-url'),
    url(r'^blink/(?P<pk>[0-9]+)/get_next/$', views.blink_get_next, name='blink-get-next'),
    url(r'^blinkAssignment/create/$', views.BlinkAssignmentCreate.as_view(), name='blinkAssignment-create'),
    url(r'^blinkAssignment/(?P<pk>[0-9]+)/start/$', views.blink_assignment_start, name='blinkAssignment-start'),
    url(r'^blinkAssignment/(?P<pk>[0-9]+)/update/$', views.BlinkAssignmentUpdate.as_view(), name='blinkAssignment-update'),
]
