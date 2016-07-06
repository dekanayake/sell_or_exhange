from django.db import models
import moneyed
from djmoney.models.fields import MoneyField
from django.db.models.signals import post_delete,post_save
from django.dispatch import receiver
import os
from django.conf import settings
from PIL import Image, ImageChops, ImageOps
import logging


# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=300)
    parentCategory =  models.ForeignKey('self',null=True,blank=True)

    def __str__(self):
        return self.getCategoryLabel()


    def getCategoryLabel(self):
        categoryArray = []
        currentCategory = self

        while (currentCategory is not None):
            categoryArray.append(currentCategory.name)
            currentCategory = currentCategory.parentCategory

        output = ""
        if (len(categoryArray) == 1):
            output = categoryArray[0]
        else:
            output = " > ".join(list(reversed(categoryArray)))

        return output


class Brand(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    def __str__(self):
        return ' :: '.join([self.category.getCategoryLabel(), self.name])

class Product(models.Model):
    PRODUCT_CONDITIONS = (
        ('N','New'),
        ('O','Used')
    )
    PRODUCT_STATUS = (
        ('CREATED','CREATED'),
        ('SUBMITTED','SUBMITTED'),
        ('APPROVED','APPROVED')
    )
    title = models.CharField(max_length=100)
    condition = models.CharField(max_length=1, choices=PRODUCT_CONDITIONS)
    description = models.TextField(max_length=20000)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10,decimal_places=2,null=True, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, null=True)
    model = models.CharField(max_length=100, null=True)
    negotiable = models.BooleanField(default=False)
    exchangeable = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=PRODUCT_STATUS,editable=False)

def generate_product_image_filename(instance, filename):
    url = "images/prod/%s/%s" % (instance.product.pk, filename)
    return url

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    fileName = models.CharField(max_length=150)
    image = models.FileField(upload_to=generate_product_image_filename)

class SelectProductAttributeValues(models.Model):
    name = models.CharField(max_length=200)
    def __str__(self):
        return  self.name

def generate_temp_image_filename(instance, filename):
    url = "images/tempory/%s/%s" % (instance.key, filename)
    return url


class TemporyProductImage(models.Model):
    key = models.CharField(max_length=150)
    fileName = models.CharField(max_length=150)
    image = models.FileField(upload_to=generate_temp_image_filename)



class ProductAttribute(models.Model):
    PRODUCT_ATTRIBUTE_TYPES = (
        ('SELECT','SELECT'),
        ('CHECKBOX','CHECKBOX'),
        ('RADIO','RADIO'),
        ('TEXT','TEXT'),
        ('NUMBER','NUMBER')
    )
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    displayLabel = models.CharField(max_length=100)
    type = models.CharField(max_length=100,choices=PRODUCT_ATTRIBUTE_TYPES)
    group = models.CharField(max_length=200, null=True, blank=True)
    selectValues = models.ManyToManyField(SelectProductAttributeValues,blank=True)
    required = models.BooleanField()
    def __str__(self):
        return ' :: '.join([self.category.getCategoryLabel(), self.name])



class ProductData(models.Model):
    productAttribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    value = models.CharField(max_length=100)

class ExchangeableProduct(models.Model):
    PRODUCT_CONDITIONS = (
        ('N','New'),
        ('O','Used')
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    exchangeWithCategory = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, null=True)
    price = models.DecimalField(max_digits=10,decimal_places=2,null=True)
    condition = models.CharField(max_length=1, choices=PRODUCT_CONDITIONS)

class ExchanableProductCriteria(models.Model):
    product = models.ForeignKey(ExchangeableProduct, on_delete=models.CASCADE)
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=100)


class ExchangeableProductCandidates(models.Model):
    product = models.ForeignKey(ExchangeableProduct, on_delete=models.CASCADE)
    exchangeProduct = models.ForeignKey(Product, on_delete=models.CASCADE)


@receiver(post_delete, sender=TemporyProductImage)
def temp_product_image_post_delete_handler(sender, **kwargs):
    productImage = kwargs['instance']
    storage, path = productImage.image.storage, productImage.image.path
    storage.delete(path)

    parentPath = "%s/images/tempory/%s" % (settings.MEDIA_ROOT,productImage.key)
    if not os.listdir(parentPath):
        os.rmdir(parentPath)



@receiver(post_save, sender=ProductImage)
def photo_image_post_save_handler(sender, **kwargs):
    productImage = kwargs['instance']
    path =  productImage.image.path

    pathWithoutExtension = path[0:path.find('.') - 1]
    fileExtension = path[path.find('.') + 1:len(path)]

    im = Image.open(path)

    thumbnailPath = "%s_thumbnail.%s" % (pathWithoutExtension,fileExtension)
    __makeThumb(path, thumbnailPath, (136,102))

    previewPath = "%s_preview.%s" % (pathWithoutExtension,fileExtension)
    __makeThumb(path, previewPath, (612,460))


def __makeThumb(f_in, f_out, size=(80,80)):

    image = Image.open(f_in)
    image.thumbnail(size, Image.ANTIALIAS)
    image_size = image.size

    thumb = ImageOps.fit(image, size, Image.ANTIALIAS, (0.5, 0.5))

    thumb.save(f_out,quality=95)


