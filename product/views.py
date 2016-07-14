from django.shortcuts import render,redirect
from django.http import HttpResponse
from .models import Category
from .models import Product
from .models import ProductData
from .models import TemporyProductImage
from .models import ProductImage
from .forms import ProductForm
import logging
from django.http import HttpResponse
import random
from django.core.files.base import ContentFile
from django.http import JsonResponse
from datetime import datetime

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
        return redirect('add_product', selected_category_id = category_id)


def add_product(request,selected_category_id,random_key = -1):
    random_number = random.getrandbits(128)
    selected_category_long_id = long(selected_category_id)
    if request.method == 'POST':
        form = ProductForm(data=request.POST,category=selected_category_long_id)
        selectedCategory = Category.objects.get(pk= selected_category_long_id)
        if form.is_valid():
            productId = __saveProduct(form, selectedCategory, random_key)
            return redirect('show_product', product_id = productId)
        else:
            return render(request, 'product/addProduct.html', {'selectedCategory':selectedCategory,'form':form})

    else:
        productForm =  ProductForm(category=selected_category_long_id)
        selectedCategory = Category.objects.get(pk= selected_category_long_id)
        return render(request, 'product/addProduct.html', {'selectedCategory':selectedCategory,'form':productForm,'randomNumber':random_number})

def show_product(request,product_id):
    loadedProduct = Product.objects.get(pk=product_id)
    loadedProductData = ProductData.objects.filter(product__pk=product_id)
    productImages = ProductImage.objects.filter(product__pk=product_id)
    firstImage = productImages[0]
    return render(request, 'product/showProduct.html',{'product':loadedProduct,'additionalProductData':loadedProductData,'productImages':productImages, 'firstImage':firstImage})

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

def product_images(request,imagePK,type):
    imageToSend = ProductImage.objects.get(pk=imagePK)
    storage, path = imageToSend.image.storage , imageToSend.image.path
    pathWithoutExtension = path[0:path.find('.') - 1]
    fileExtension = path[path.find('.') + 1:len(path)]
    if type is 'zoom':
        requestedPath = path
    else:
        requestedPath =    "%s_%s.%s" % (pathWithoutExtension,type,fileExtension)

    return HttpResponse(storage.open(requestedPath).read(), content_type="image/jpeg")

def __saveProduct(productForm, selectedCategory, randomKey):
    savedProduct  = productForm.save(commit=False)
    savedProduct.category = selectedCategory
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

    logging.warning(savedProduct.id)
    return savedProduct.id











