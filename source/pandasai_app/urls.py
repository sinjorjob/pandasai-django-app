from django.urls import path
from .views import main_views, model_settings_views

urlpatterns = [
    path('', main_views.index, name='index'),
    path('save_model_settings/', model_settings_views.save_model_settings, name='save_model_settings'),
    path('get_model_settings/', model_settings_views.get_model_settings, name='get_model_settings'),
    path('get_model_names/', model_settings_views.get_model_names, name='get_model_names'),
]