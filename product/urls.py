from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^selectCategory/(?P<category_id>[0-9]+)', views.select_category, name='select_category'),
    url(r'^selectCategory', views.select_category, name='select_category'),
    url(r'^showAddProduct/(?P<selected_category_id>[0-9]+)', views.show_add_product, name='show_add_product'),
]