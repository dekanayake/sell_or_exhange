from haystack import indexes
from celery_haystack.indexes import CelerySearchIndex
from .models import Product
from .models import ProductData
from .models import ProductDataSelectValue
import logging
import datetime



class ProductIndex(CelerySearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    condition  = indexes.CharField(model_attr='condition',faceted=True)
    category = indexes.MultiValueField(faceted=True)
    variants = indexes.MultiValueField(faceted=True)
    price = indexes.DecimalField(model_attr='price',null=True)
    brand = indexes.CharField(model_attr='brand',faceted=True,null=True)
    negotiable = indexes.BooleanField(model_attr='negotiable')
    exchangeable = indexes.BooleanField(model_attr='exchangeable')
    status = indexes.CharField(model_attr='status')
    postedDate = indexes.DateTimeField(model_attr='postedDate')
    title = indexes.CharField(model_attr='title',indexed=False)
    description = indexes.CharField(model_attr='description',indexed=False)

    def get_model(self):
        return Product

    def prepare_brand(self,obj):
            return obj.brand.name

    def prepare_condition(self,obj):
        return dict(Product.PRODUCT_CONDITIONS).get(obj.condition)

    def prepare_postedDate(self,obj):
        return obj.postedDate.strftime('%Y-%m-%dT%H:%M:%SZ')

    def prepare_category(self, obj):
        output = []
        currentCategory = obj.category
        categoryArray = []
        while (currentCategory is not None):
            categoryArray.append(currentCategory.pk)
            currentCategory = currentCategory.parentCategory

        return categoryArray

    def prepare_variants(self, obj):
        output = []
        productDataList =  ProductData.objects.filter(product__pk=long(obj.pk))
        for productDataItem in productDataList:
            if productDataItem.productAttribute.type in ['CHECKBOX','SELECT','RADIO']:
                productDataSelectValues = ProductDataSelectValue.objects.filter(productData__pk=long(productDataItem.pk))
                for productDataSelectItem in productDataSelectValues:
                    output.append('>'.join([str(productDataItem.productAttribute.pk),str(productDataSelectItem.selectValue.pk)]))
        return output



