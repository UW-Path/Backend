"""uwpath_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, re_path
from django.contrib import admin

import app.view as uwPath
import app.views.course_view as course_view
import app.views.prereq_view as prereq_view
import app.views.antireq_view as antireq_view
import app.views.breath_view as breath_view
import app.views.requirement_view as requirement_view
import app.views.validation_view as validation_view
import app.views.communication_view as communication_view
import app.views.validation_view as validation_view
import app.views.email_view as email_view


urlpatterns = [
    path('', uwPath.index, name='index'),
    path(r'admin/', admin.site.urls),
    path(r'api/', uwPath.AllApp.as_view()),
    path(r'api/course-info/get', course_view.Course_Info_API.as_view()),
    path(r'api/course-info/filter', course_view.Course_Info_API.filter),
    path(r'api/course-info/', course_view.Course_Info_List.as_view()),
    path(r'api/prereqs/', prereq_view.Prereqs_List.as_view()),
    path(r'api/prereqs/get', prereq_view.Prereqs_API.as_view()),
    path(r'api/antireqs/', antireq_view.Antireqs_List.as_view()),
    path(r'api/antireqs/get', antireq_view.Antireqs_API.as_view()),
    path(r'api/breath/', breath_view.Breath_List.as_view()),
    path(r'api/breath/get', breath_view.Breath_API.as_view()),
    path(r'api/breath_met/', breath_view.BreathAPI.as_view()),
    path(r'api/requirements/', requirement_view.Requirements_List.as_view()),
    path(r'api/requirements/get', requirement_view.Requirements_API.as_view()),
    path(r'api/requirements/requirements', requirement_view.Requirements_API.requirements),
    path(r'api/requirements/unique_major', requirement_view.Requirements_List.get_unique_major),
    path(r'api/requirements/get_available_year_for_program', requirement_view.Requirements_List.get_available_year_for_program),
    path(r'api/requirements/export', requirement_view.Requirements_API.download_course_schedule),
    path(r'api/meets_prereqs/get', validation_view.UWPath_API.as_view()),
    path(r'api/communications/', communication_view.Communications_List.as_view()),
    path(r'api/communications/get', communication_view.Communications_API.as_view()),
    path(r'api/send_email', email_view.email_API.as_view()),


    path(r'contact', uwPath.contact, name='contact'),
    re_path(r'(?P<pk>\d+)', uwPath.AppView.as_view()),
]
