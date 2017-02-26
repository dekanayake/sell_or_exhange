from django.shortcuts import render,redirect
from django.http import HttpResponse
from .models import Category
from .models import Location
from .models import Product
from .models import ProductData
from .models import TemporyProductImage
from .models import ProductImage
from .forms import ProductForm
from .forms import ProductSearchForm
from .forms import ProductDataSelectValue
from .forms import SelectProductAttributeValues
from .forms import ProductAttribute
import logging
from django.http import HttpResponse
import random
import re
from django.core.files.base import ContentFile
from django.http import JsonResponse
from datetime import datetime
import operator
import urllib

# Create your views here.

def select_category(request,category_id="-1"):
    categoryList = []
    selectedCategory = ""
    noChild = False
    category_id_long_value = -1


    if (category_id == "-1"):
        categoryList = Category.objects.filter(parentCategory__isnull = True)
    else:
        category_id_long_value = long(category_id)
        selectedCategory = Category.objects.get(pk= category_id_long_value)
        categoryList = Category.objects.filter(parentCategory__id = category_id_long_value)

    categoryChildExists = categoryList.exists()
    if (categoryChildExists):
        return render(request, 'product/selectCategory.html', {'categoryList': categoryList,'selectedCategory':selectedCategory,'noChild':noChild})
    else:
        return redirect('%s?%s' % ('/products/selectLocation',urllib.urlencode({'category':selectedCategory.id})))

def select_location(request,location_id="-1"):
    locationList = []
    selectedLocation = ""
    noChild = False
    location_id_long_value = -1

    categoryID = long(request.GET.get('category'))
    selectedCategory = Category.objects.get(pk=categoryID)


    if (location_id == "-1"):
        locationList = Location.objects.filter(parentLocation__isnull = True)
    else:
        location_id_long_value = long(location_id)
        selectedLocation = Location.objects.get(pk= location_id_long_value)
        locationList = Location.objects.filter(parentLocation__id = location_id_long_value)

    locationChildExists = locationList.exists()
    if (locationChildExists):
        return render(request, 'product/selectLocation.html', {'locationList': locationList,'selectedLocation':selectedLocation,'selectedCategory':selectedCategory})
    else:
        return redirect('add_product', selected_category_id = categoryID, selected_location_id = location_id)



def add_product(request,selected_category_id, selected_location_id,random_key = -1):
    selectedCategory = Category.objects.get(pk= long(selected_category_id))
    selectedLocation = Location.objects.get(pk= long(selected_location_id))
    if request.method == 'POST':
        form = ProductForm(data=request.POST,category=long(selected_category_id))
        if form.is_valid():
            productId = __saveProduct(form, selectedCategory, selectedLocation, random_key)
            return redirect('show_product', product_id = productId)
        else:
            logging.warning('---------------------------------------------------------')
            logging.warning(random_key)
            return render(request, 'product/addProduct.html', {'selectedCategory':selectedCategory,'selectedLocation':selectedLocation,'form':form,'randomNumber':random_key})
    else:
        random_number = random.getrandbits(128)
        productForm =  ProductForm(category=long(selected_category_id))
        return render(request, 'product/addProduct.html', {'selectedCategory':selectedCategory,'selectedLocation':selectedLocation,'form':productForm,'randomNumber':random_number})

def update_product(request,product_id):
    productInstance = Product.objects.get(pk=product_id)
    selectedCategory = Category.objects.get(pk= long(productInstance.category.id))
    selectedLocation = Location.objects.get(pk= long(productInstance.location.id))
    productForm = ProductForm(instance=productInstance,category=long(productInstance.category.id))
    __create_temp_product_images_from_images_of_saved_product(productInstance.pk)
    return render(request, 'product/addProduct.html', {'selectedCategory':selectedCategory,'selectedLocation':selectedLocation,'form':productForm,'randomNumber':productInstance.pk,'status':'update'})


def show_product(request,product_id):
    loadedProduct = Product.objects.get(pk=product_id)
    loadedProductDataList = ProductData.objects.filter(product__pk=product_id)
    loadedProductMap = {}
    featuresList = []
    for loadedProductData in loadedProductDataList:
        if loadedProductData.productAttribute.name == 'features':
            featuresList = ProductDataSelectValue.objects.filter(productData__pk=loadedProductData.id)
            logging.warning(featuresList)
        else:
            if loadedProductData.productAttribute.type in ['RADIO','SELECT','CHECKBOX']:
                loadedProductMap[loadedProductData] = ProductDataSelectValue.objects.filter(productData__pk=loadedProductData.id)
            else:
                loadedProductMap[loadedProductData] = []
    productImages = ProductImage.objects.filter(product__pk=product_id)
    firstImage = productImages[0]
    return render(request, 'product/showProduct.html',{'product':loadedProduct,'additionalProductData':loadedProductMap,'features':featuresList,'productImages':productImages, 'firstImage':firstImage})

def temp_product_images(request,random_number):

    if request.method == 'POST':
        fileNameArray = []
        for index in range(0, 9):
            files = request.FILES.getlist("file[{}]".format(index))
            for file in files:
               tmpFile =   TemporyProductImage()
               tmpFile.key =  random_number
               tmpFile.fileName = file.name
               tmpFile.image.save(file.name,ContentFile(file.read()), save=True )
               fileNameArray.append(file.name)
        return  JsonResponse(fileNameArray, safe=False)
    elif request.method == 'DELETE':
        fileNameToDelete = request.DELETE['fileName']
        TemporyProductImage.objects.get(key=random_number,fileName=fileNameToDelete).delete()
        return HttpResponse(status=200)


def __create_temp_product_images_from_images_of_saved_product(product_id):
    TemporyProductImage.objects.filter(key=product_id).delete()

    savedProductImages = ProductImage.objects.filter(product__pk=product_id)
    for savedProductImage in savedProductImages:
        tmpFile =   TemporyProductImage()
        tmpFile.key =  product_id
        tmpFile.fileName = savedProductImage.fileName
        tmpFile.image.save(savedProductImage.fileName,ContentFile(savedProductImage.image.read()), save=True)

def get_uploaded_image_files(request, productID):
    temportProductImages = TemporyProductImage.objects.filter(key=productID)
    tempryImageIDArray = []
    for temporyProductImage in temportProductImages:
        tempryImageIDArray.append({'fileName' : temporyProductImage.fileName,'imageId' : temporyProductImage.pk, 'size': temporyProductImage.image.size})
    return  JsonResponse(tempryImageIDArray, safe=False)


def product_images(request,imagePK,type):
    imageToSend = ProductImage.objects.get(pk=imagePK)
    storage, path = imageToSend.image.storage , imageToSend.image.path
    pathWithoutExtension = path[0:path.find('.') - 1]
    fileExtension = path[path.find('.') + 1:len(path)]

    if type == 'zoom':
        requestedPath = path
    else:
        requestedPath =    "%s_%s.%s" % (pathWithoutExtension,type,fileExtension)

    return HttpResponse(storage.open(requestedPath).read(), content_type="image/jpeg")


def tempory_product_image_thumbnail(request,imagePK):
    temporyImageToSend = TemporyProductImage.objects.get(pk=imagePK)
    storage, path = temporyImageToSend.image.storage , temporyImageToSend.image.path
    pathWithoutExtension = path[0:path.find('.') - 1]
    fileExtension = path[path.find('.') + 1:len(path)]

    requestedPath =    "%s_%s.%s" % (pathWithoutExtension,'thumbnail',fileExtension)

    return HttpResponse(storage.open(requestedPath).read(), content_type="image/jpeg")


def __saveProduct(productForm, selectedCategory,selectedLocation, randomKey):
    savedProduct  = productForm.save(commit=False)
    savedProduct.category = selectedCategory
    savedProduct.location = selectedLocation
    savedProduct.status = 'CREATED'
    savedProduct.postedDate = datetime.now()
    savedProduct.save()

    productDataList = productForm.get_product_data_list()
    for productData, productDataSelectList in productDataList:
        productData.product = savedProduct
        productData.save()

        for productDataSelect in productDataSelectList:
            logging.warning(productData)
            productDataSelect.productData = productData
            productDataSelect.save()


    for temporyProductImage in TemporyProductImage.objects.filter(key=randomKey):
        productImage = ProductImage()
        productImage.product = savedProduct
        productImage.fileName = temporyProductImage.fileName
        productImage.image.save(temporyProductImage.fileName,ContentFile(temporyProductImage.image.read()), save=True)
        temporyProductImage.delete()

    savedProduct.save()

    logging.warning(savedProduct.id)
    return savedProduct.id















