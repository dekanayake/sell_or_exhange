from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    url(r'^selectCategory/(?P<category_id>[0-9]+)', views.select_category, name='select_category'),
    url(r'^selectCategory', views.select_category, name='select_category'),
    url(r'^addProduct/(?P<selected_category_id>[0-9]+)/(?P<random_key>[0-9]+)', views.add_product, name='add_product'),
    url(r'^addProduct/(?P<selected_category_id>[0-9]+)', views.add_product, name='add_product'),
    url(r'^showProduct/(?P<product_id>[0-9]+)', views.show_product, name='show_product'),
    url(r'^tmpProductImages/(?P<random_number>[0-9]+)', views.temp_product_images, name='temp_product_images'),
    url(r'^productImages/(?P<imagePK>[0-9]+)/(?P<type>\w+)', views.product_images, name='product_images'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)