from django.contrib import admin

from .models import Category
from .models import Location
from .models import Brand
from .models import ProductAttribute
from .models import SelectProductAttributeValues

# Register your models here.
admin.site.register(Category)
admin.site.register(Location)
admin.site.register(Brand)
admin.site.register(ProductAttribute)
admin.site.register(SelectProductAttributeValues)
