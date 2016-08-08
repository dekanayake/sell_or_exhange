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
import re
from django.core.files.base import ContentFile
from django.http import JsonResponse
from datetime import datetime
from haystack.views import FacetedSearchView
from haystack.query import SearchQuerySet
from haystack.generic_views import FacetedSearchView as BaseFacetedSearchView
from django.forms.models import model_to_dict
from cacheops import cached_as
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
        ProductSearchView.__updateVariantFacetCounts(self.request, context, facet_fields)

        context.update({'categoryList' : ProductSearchView.__getCategoryTree()})
        if "category" in facet_fields:
            ProductSearchView.__updateCategoryFacetCounts(self.request, facet_fields['category'],context)



        return context

    @staticmethod
    def __updateCategoryFacetCounts(request,facet_fields,context):
        selected_category = None

        selected_facets = dict(map(lambda i:  (i.split(':',1)[0],i.split(':',1)[1]),request.GET.getlist("selected_facets")))
        if ('category_exact' in selected_facets):
            selected_category = selected_facets['category_exact']

        if not selected_category:
            selected_category = request.GET.get('category')


        @cached_as(Category, extra=selected_category)
        def __getParentCategoryTree():
            parentCategoryList = []
            if (selected_category and (not selected_category == "-1")):
                currentCategory = Category.objects.get(pk=long(selected_category))
                if not currentCategory.category_set.all():
                    parentCategory = currentCategory.parentCategory
                else:
                    parentCategory = currentCategory
                parentCategoryList = []
                while (parentCategory is not None):
                    parentCategoryList.append((parentCategory.pk,parentCategory.name))
                    parentCategory = parentCategory.parentCategory

            parentCategoryDict = {}
            tempParentCategoryDict = parentCategoryDict
            childCategoryDict = {}
            parentCatogries = [(-1,'All categories')] + list(reversed(parentCategoryList))
            for parentCategory in parentCatogries:
                childCategoryDict = {}
                tempParentCategoryDict[parentCategory] = childCategoryDict
                tempParentCategoryDict = childCategoryDict

            return parentCategoryDict

        @cached_as(Category, extra=selected_category)
        def __getChildCategories():
            if (selected_category and (not selected_category == "-1")):
                currentCategory = Category.objects.get(pk=long(selected_category))
                childCategories  = currentCategory.category_set.all()
                if not childCategories:
                    childCategories = Category.objects.get(pk=currentCategory.parentCategory.pk).category_set.all()
            else:
                childCategories  = ProductSearchView.__getParentCategories()
            return childCategories

        @cached_as(Category, extra=selected_category)
        def __getSelectedCategory():
            if selected_category == "-1":
                return (-1,"All categories")
            else:
                currentCategory = Category.objects.get(pk=long(selected_category))
                return (currentCategory.pk, currentCategory.name)


        facetFieldsDict = dict(map(lambda i: (i[0],i[1]), facet_fields))
        childCategoryArray = []
        for childCategory in __getChildCategories():
            if str(childCategory.pk) in facetFieldsDict:
                childCategoryArray.append((childCategory.pk,childCategory.name, facetFieldsDict[str(childCategory.pk)]))


        context.update({'category_facet_category_tree':__getParentCategoryTree()})
        context.update({'category_facet_child_categories':childCategoryArray})
        if selected_category:
            context.update({'selected_category':__getSelectedCategory()})
        context.update({'category_selected_facet_url':ProductSearchView.__removeParamsFromURL(request.get_full_path(),['&selected_facets=category_exact:.*','&category=.*'])})
        category_facet_hide = request.GET.get('category_facet_hide')
        if category_facet_hide:
            context.update({'category_facet_hide':True})
            context.update({'category_facet_expand_url':ProductSearchView.__removeParamsFromURL(request.get_full_path(),['&category_facet_hide=Y'])})

    @staticmethod
    def __updateVariantFacetCounts(request, context, facet_fields):
        variants_facets = []
        if 'variants' in facet_fields:
            variants_facets = facet_fields['variants']
        variants_facet_dict = {}
        for variant_facet in variants_facets:
            attribute = ProductAttribute.objects.get(pk=long(variant_facet[0].split('>',1)[0]))
            selectValue = SelectProductAttributeValues.objects.get(pk=long(variant_facet[0].split('>',1)[1]))
            variants_facet_dict.setdefault(attribute,[]).append((variant_facet[0],selectValue,variant_facet[1]))

        variant_facet_hidden_facets_dict = {}
        for attribute in variants_facet_dict:
            variant_facet_hide_status = request.GET.get('variant_facet_%s_hide' % attribute.pk)
            if variant_facet_hide_status:
                variant_facet_hidden_facets_dict[attribute.pk] = ProductSearchView.__removeParamsFromURL(request.get_full_path(),["&variant_facet_%s_hide=Y" % (attribute.pk)])


        sorted_variants_facet_dict =  dict(sorted(variants_facet_dict.items(), key=operator.itemgetter(0)))
        context.update({'variants_facets_dict':sorted_variants_facet_dict})

        selected_facets_or = map(lambda i:  (i.split(':',1)[0],i.split(':',1)[1]),request.GET.getlist("selected_facets_or"))
        selected_variants_or = map(lambda i: i[1],filter(lambda i : i[0] == 'variants_exact' , selected_facets_or))
        selected_variant_names = {}
        selected_variants_or_url_dict = {}
        for selected_variant_or in selected_variants_or:
            selected_attribute = ProductAttribute.objects.get(pk=long(selected_variant_or.split('>',1)[0])).pk
            selected_facet_name = SelectProductAttributeValues.objects.get(pk=long(selected_variant_or.split('>',1)[1])).name
            selected_variant_names.setdefault(selected_attribute,[]).append((selected_variant_or,selected_facet_name))
            selected_variants_or_url_dict[selected_variant_or] = ProductSearchView.__removeParamsFromURL(request.get_full_path(),["&selected_facets_or=variants_exact:%s" % (urllib.quote(selected_variant_or))])

        if (selected_variants_or):
            context.update({'variants_facets_selected_variant_names':selected_variant_names})
            logging.warn('=======================selected_variant_names=========')
            logging.warn(selected_variant_names)
            context.update({'variants_facets_selected_variants':selected_variants_or})
            context.update({'variants_facets_selected_variants_or_url_dict':selected_variants_or_url_dict})

        context.update({'variant_facet_hidden_facets_dict':variant_facet_hidden_facets_dict})



    @staticmethod
    def __removeParamsFromURL(requestURL, regxToRemoveList):
        url = requestURL
        for regxPattern in regxToRemoveList:
            url = re.sub(regxPattern,'',url)
        return url


    @staticmethod
    @cached_as(Category)
    def __getParentCategories():
        return Category.objects.filter(parentCategory__isnull = True)

    @staticmethod
    @cached_as(Category)
    def __getCategoryTree():

        categoryList = Category.objects.all()
        categoryDict = {}
        for category in categoryList:
            parentCategoryID = -1
            if category.parentCategory:
                parentCategoryID = category.parentCategory.pk

            categoryDict.setdefault(parentCategoryID,[]).append(category)

        categoryList = categoryDict[-1]
        categoryListTmp = []


        categoryTree = {}
        while categoryList:
            for category in categoryList:
                childTree = {}
                if category.parentCategory:
                    childTree = categoryTree.get((category.parentCategory.pk,category.parentCategory.name))

                nodeTree = {}
                childTree[(category.pk,category.name)] = nodeTree
                categoryTree[(category.pk,category.name)] = nodeTree
                if category.pk in categoryDict:
                    categoryListTmp.append(categoryDict[category.pk])

            categoryList =  [val for sublist in categoryListTmp for val in sublist]
            categoryListTmp = []


        newTree = {k: v for k, v in categoryTree.items() if k[0] in map(lambda i : i.pk ,categoryDict[-1])}
        return newTree



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















