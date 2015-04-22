# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import include, url

from . import admin_views
from . import views

urlpatterns = [
    url(r'^$', views.AssignmentListView.as_view(), name='assignment-list'),
    url(r'^assignment/(?P<assignment_id>[^/]+)/', include([
        url(r'^$', views.QuestionListView.as_view(), name='question-list'),
        url(r'(?P<question_id>\d+)/', include([
            url(r'^$', views.QuestionStartView.as_view(), name='question-start'),
            url(r'^review$', views.QuestionReviewView.as_view(), name='question-review'),
            url(r'^summary$', views.QuestionSummaryView.as_view(), name='question-summary'),
        ])),
    ])),
    url(r'^admin/peerinst/', include([
        url(r'^assignment_results/(?P<assignment_id>[^/]+)/', include([
            url(r'^$', admin_views.AssignmentResultsView.as_view(), name='assignment-results'),
        ])),
    ])),
]
