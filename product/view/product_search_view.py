from haystack.generic_views import FacetedSearchView as BaseFacetedSearchView
from haystack.views import FacetedSearchView
from cacheops import cached_as
import operator
import urllib
from product.forms import ProductSearchForm
from product.models import ProductDataSelectValue
from  product.models import SelectProductAttributeValues
from  product.models import ProductAttribute
from  product.models import Category
import re
import logging

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

        if "condition" in facet_fields:
            ProductSearchView.__updateFacetCounts(self.request,'condition', facet_fields['condition'],context)

        if "brand" in facet_fields:
            ProductSearchView.__updateFacetCounts(self.request,'brand', facet_fields['brand'],context)

        ProductSearchView.__updatePriceRangeFacet(self.request, context)

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
    def __updateFacetCounts(request, facet_name, facet_fields, context):
        selected_facet = None
        facet_phrase = '%s_exact' % facet_name

        selected_facets = dict(map(lambda i:  (i.split(':',1)[0],i.split(':',1)[1]),request.GET.getlist("selected_facets")))
        if (facet_phrase in selected_facets):
            selected_facet = selected_facets[facet_phrase]

        context.update({'%s_facet_fields' % facet_name:facet_fields})
        if selected_facet:
            context.update({'%s_facet_selected_facet' % facet_name: selected_facet})
        selected_facet_url = ProductSearchView.__removeParamsFromURL(request.get_full_path(),['&selected_facets=%s_exact:.*' % facet_name])
        context.update({'%s_facet_selected_facet_url' % facet_name: selected_facet_url })

        facet_hide = request.GET.get('%s_facet_hide' % facet_name)
        if facet_hide:
            context.update({'%s_facet_hide' % facet_name:True})
            context.update({'%s_facet_expand_url' % facet_name:ProductSearchView.__removeParamsFromURL(request.get_full_path(),['&%s_facet_hide=Y' % facet_name])})


    @staticmethod
    def __updatePriceRangeFacet(request, context):
        minPrice = request.GET.get('minPrice')
        if minPrice:
            context.update({'price_facet_min_price':minPrice})

        maxPrice = request.GET.get('maxPrice')
        if maxPrice:
            context.update({'price_facet_max_price':maxPrice})

        price_filter_url = ProductSearchView.__removeParamsFromURL(request.get_full_path(),['&minPrice=.*','&maxPrice=.*'])
        context.update({'price_facet_filter_url':price_filter_url})

        facet_hide = request.GET.get('price_facet_hide')
        if facet_hide:
            context.update({'price_facet_hide':True})
            context.update({'price_facet_expand_url' :ProductSearchView.__removeParamsFromURL(request.get_full_path(),['&price_facet_hide=Y'])})


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

        selected_facets = map(lambda i:  (i.split(':',1)[0],i.split(':',1)[1]),request.GET.getlist("selected_facets"))
        selected_variants = map(lambda i: i[1],filter(lambda i : i[0] == 'variants_exact' , selected_facets))
        selected_variants_url_dict = {}
        for selected_variant in selected_variants:
            selected_attribute = ProductAttribute.objects.get(pk=long(selected_variant.split('>',1)[0])).pk
            selected_facet_name = SelectProductAttributeValues.objects.get(pk=long(selected_variant.split('>',1)[1])).name
            selected_variant_names[selected_attribute] = (selected_variant,selected_facet_name)
            selected_variants_url_dict[selected_variant] = ProductSearchView.__removeParamsFromURL(request.get_full_path(),["&selected_facets=variants_exact:%s" % (urllib.quote(selected_variant))])

        if (selected_variants_or + selected_variants):
            context.update({'variants_facets_selected_variant_names':selected_variant_names})
            context.update({'variants_facets_selected_variants':selected_variants_or + selected_variants})

        if selected_variants_or_url_dict:
            context.update({'variants_facets_selected_variants_or_url_dict':selected_variants_or_url_dict})

        if selected_variants_url_dict:
            context.update({'variants_facets_selected_variants_url_dict':selected_variants_url_dict})

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