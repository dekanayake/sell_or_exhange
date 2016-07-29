from django.shortcuts import render,redirect
from django.http import HttpResponse
from .models import Category
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
from django.core.files.base import ContentFile
from django.http import JsonResponse
from datetime import datetime
from haystack.views import FacetedSearchView
from haystack.query import SearchQuerySet
from haystack.generic_views import FacetedSearchView as BaseFacetedSearchView

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
    logging.warning('this is the additionalProductData')
    logging.warning(loadedProductMap)
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

class ProductSearchView(BaseFacetedSearchView):
    template_name = 'product/product_search.html'
    form_class = ProductSearchForm
    facet_fields = ['category']

    def get_form_kwargs(self):
        kwargs = super(ProductSearchView, self).get_form_kwargs()
        kwargs.update({
            'selected_facets_or': self.request.GET.getlist("selected_facets_or")
        })
        return kwargs

    def get_queryset(self):
        qs = super(ProductSearchView, self).get_queryset()
        selected_facets = list(set(map(lambda i:  i.split(':',1)[0],self.request.GET.getlist("selected_facets"))))
        selected_category = self.request.GET.get('category')

        if (selected_category) or ('category_exact' in selected_facets):
            for facet_field in ['category','condition','brand','variants']:
                qs = qs.facet(facet_field)

        return qs


    def get_context_data(self, **kwargs):
        context = super(ProductSearchView, self).get_context_data(**kwargs)
        facet_fields = self.queryset.facet_counts()['fields']
        if 'variants' in facet_fields:
            variants_facets = facet_fields['variants']
            variants_facet_dict = {}
            for variant_facet in variants_facets:
               attribute = ProductAttribute.objects.get(pk=long(variant_facet[0].split('>',1)[0])).displayLabel
               selectValue = SelectProductAttributeValues.objects.get(pk=long(variant_facet[0].split('>',1)[1])).name
               variants_facet_dict.setdefault(attribute,[]).append((selectValue,variant_facet[1]))
            context.update({'variants':variants_facet_dict})



        return context




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

    savedProduct.save()


    for temporyProductImage in TemporyProductImage.objects.filter(key=randomKey):
        productImage = ProductImage()
        productImage.product = savedProduct
        productImage.fileName = temporyProductImage.fileName
        productImage.image.save(temporyProductImage.fileName,ContentFile(temporyProductImage.image.read()), save=True)
        temporyProductImage.delete()

    logging.warning(savedProduct.id)
    return savedProduct.id











