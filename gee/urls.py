from django.contrib import admin
from django.urls import path, include
from gee.views import CalculatedMapsAPI
from gee.views import DatesWithImages
from gee.views import TimeSeriesView

urlpatterns = [
    path('calculated-maps/', CalculatedMapsAPI.as_view()),
    path('dates-data/', DatesWithImages.as_view()),
    path('time-series/', TimeSeriesView.as_view()),
]
