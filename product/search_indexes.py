from haystack import indexes
from celery_haystack.indexes import CelerySearchIndex
from .models import Product
from .models import Location
from .models import ProductData
from .models import ProductDataSelectValue
from .models import ProductImage
import logging
import datetime
import requests
from django.conf import settings
from cacheops import cached_as



class ProductIndex(CelerySearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    condition  = indexes.CharField(model_attr='condition',faceted=True)
    category = indexes.MultiValueField(faceted=True)
    location = indexes.MultiValueField(faceted=True)
    variants = indexes.MultiValueField(faceted=True)
    price = indexes.FloatField(model_attr='price',null=True)
    brand = indexes.CharField(model_attr='brand',faceted=True,null=True)
    negotiable = indexes.BooleanField(model_attr='negotiable')
    exchangeable = indexes.BooleanField(model_attr='exchangeable')
    status = indexes.CharField(model_attr='status')
    postedDate = indexes.DateTimeField(model_attr='postedDate')
    title = indexes.CharField(model_attr='title',indexed=False)
    description = indexes.CharField(model_attr='description',indexed=False)
    previewImageURL = indexes.CharField(indexed=False)
    thumbnailImageURL = indexes.CharField(indexed=False)
    geoLocation = indexes.LocationField(null=True)

    def get_model(self):
        return Product

    def prepare_brand(self,obj):
            return obj.brand.name

    def prepare_geoLocation(self,obj):
        locationName = obj.location.name

        @cached_as(Location,extra=locationName)
        def __getCorrdinates():
            payload = {'address': locationName, 'components':'country:%s' % settings.GOOGLE_MAP_API_SEARCH_COUNTRY_CODE,'key': settings.GOOGLE_MAP_API_KEY}
            request = requests.get(settings.GOOGLE_MAP_API_RESUORCE_URL, params=payload)
            result = request.json()
            if (result["status"] == "OK"):
                lat = request.json()["results"][0]['geometry']['location']["lat"]
                lng = request.json()["results"][0]['geometry']['location']["lng"]
                return "%s,%s" % (lat, lng)
            else:
                return None

        result = __getCorrdinates()
        return result



    def prepare_condition(self,obj):
        return dict(Product.PRODUCT_CONDITIONS).get(obj.condition)

    def prepare_previewImageURL(self,obj):
        productImages = ProductImage.objects.filter(product__pk=obj.pk)
        if productImages:
            firstImage = productImages[0]
            imageToSend = ProductImage.objects.get(pk=firstImage.pk)
            url = imageToSend.image.url
            pathWithoutExtension = url[0:url.find('.') - 1]
            fileExtension = url[url.find('.') + 1:len(url)]
            url =    "%s_%s.%s" % (pathWithoutExtension,'preview',fileExtension)
            return url
        else:
            return 'NONE'

    def prepare_thumbnailImageURL(self,obj):
        productImages = ProductImage.objects.filter(product__pk=obj.pk)
        if productImages:
            firstImage = productImages[0]
            imageToSend = ProductImage.objects.get(pk=firstImage.pk)
            url = imageToSend.image.url
            pathWithoutExtension = url[0:url.find('.') - 1]
            fileExtension = url[url.find('.') + 1:len(url)]
            url =    "%s_%s.%s" % (pathWithoutExtension,'thumbnail',fileExtension)
            return url
        else:
            return 'NONE'



    def prepare_postedDate(self,obj):
        return obj.postedDate.strftime('%Y-%m-%dT%H:%M:%SZ')

    def prepare_category(self, obj):
        output = []
        currentCategory = obj.category
        categoryArray = []
        while (currentCategory is not None):
            categoryArray.append(currentCategory.pk)
            currentCategory = currentCategory.parentCategory

        return categoryArray + [-1]

    def prepare_location(self, obj):
        output = []
        currentLocation = obj.location
        locationArray = []
        while (currentLocation is not None):
            locationArray.append(currentLocation.pk)
            currentLocation = currentLocation.parentLocation

        return locationArray + [-1]

    def prepare_variants(self, obj):
        output = []
        productDataList =  ProductData.objects.filter(product__pk=long(obj.pk))
        for productDataItem in productDataList:
            if productDataItem.productAttribute.type in ['CHECKBOX','SELECT','RADIO']:
                productDataSelectValues = ProductDataSelectValue.objects.filter(productData__pk=long(productDataItem.pk))
                for productDataSelectItem in productDataSelectValues:
                    output.append('>'.join([str(productDataItem.productAttribute.pk),str(productDataSelectItem.selectValue.pk)]))
        return output



