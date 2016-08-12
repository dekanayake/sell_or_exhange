from django import forms
from .models import Product
from .models import ProductAttribute
from .models import SelectProductAttributeValues
from .models import ProductDataSelectValue
from .models import Brand
from .models import ProductData
from django_summernote.widgets import SummernoteWidget
import logging
from django.utils.safestring import mark_safe
from haystack.forms import FacetedSearchForm





class ProductForm(forms.ModelForm):

    featureElements =  {}
    choiceElements = []
    radioElements = []
    additionalAttributes = []



    class Meta:
        model = Product
        fields = ['title','condition','description','price','negotiable','exchangeable','brand','model','contactNumber','email']



    def __init__(self, *args, **kwargs):
        self.featureElements = {}
        self.choiceElements = []
        self.radioElements = []
        self.additionalAttributes = []
        selectedCategory = kwargs.pop('category')
        super(ProductForm, self).__init__(*args, **kwargs)
        brands = tuple((brand.id, brand.name) for brand in Brand.objects.filter(category__pk=long(selectedCategory)))
        self.fields['brand'].choices = brands
        self.fields['description']=  forms.CharField(widget=SummernoteWidget())
        productAttributes = ProductAttribute.objects.filter(category__pk=long(selectedCategory))
        for productAttribute in productAttributes:

            group = productAttribute.group
            if group is None:
                group = 'EMPTY'

            self.featureElements.setdefault(str(group), []).append(productAttribute.name)
            self.additionalAttributes.append(productAttribute)

            if productAttribute.type == 'SELECT':
                selectValues = tuple((str(selectValue.pk), self.__get_render_choice(selectValue,productAttribute.showIcons)) for selectValue in productAttribute.selectValues.all())
                self.fields[productAttribute.name] =  forms.ChoiceField(choices=selectValues,required=productAttribute.required)
            if productAttribute.type == 'CHECKBOX':
                selectValues = tuple((str(selectValue.pk), self.__get_render_choice(selectValue,productAttribute.showIcons)) for selectValue in productAttribute.selectValues.all())
                self.fields[productAttribute.name] =  forms.MultipleChoiceField(choices=selectValues,required=productAttribute.required)
                self.choiceElements.append(productAttribute.name)
            if productAttribute.type == 'RADIO':
                selectValues = tuple((str(selectValue.pk), self.__get_render_choice(selectValue,productAttribute.showIcons)) for selectValue in productAttribute.selectValues.all())
                self.fields[productAttribute.name] =  forms.ChoiceField(choices=selectValues,required=productAttribute.required)
                self.radioElements.append(productAttribute.name)
            if productAttribute.type == 'TEXT':
                self.fields[productAttribute.name] =  forms.CharField(required=productAttribute.required)
            if productAttribute.type == 'NUMBER':
                self.fields[productAttribute.name] =  forms.IntegerField(required=productAttribute.required)


    def __get_render_choice(self, value, showIcon):
        if showIcon:
            return mark_safe("<img src='%s'/> %s" % (value.icon.url, value.name))
        else:
            return value.name



    def get_product_data_list(self):
            productDataList = []
            for productAttribute in self.additionalAttributes:
                selectValueList = []
                productDataSelectList = []
                productData = ProductData()
                productData.productAttribute = productAttribute
                elementValue = self.cleaned_data[productAttribute.name]
                logging.warn(productAttribute.name)
                logging.warn(elementValue)
                if productAttribute.type in ['CHECKBOX']:
                    selectValueList = elementValue
                elif productAttribute.type in ['SELECT','RADIO']:
                    selectValueList = [elementValue]
                else:
                    productData.value = elementValue
                for selectValue in selectValueList:
                    productDataSelectValue =  ProductDataSelectValue()
                    selectProductAttributeValue = SelectProductAttributeValues.objects.get(pk=selectValue)
                    productDataSelectValue.productData = productData
                    productDataSelectValue.selectValue = selectProductAttributeValue
                    productDataSelectList.append(productDataSelectValue)

                productDataList.append((productData, productDataSelectList))
            return productDataList



class ProductSearchForm(FacetedSearchForm):

    def __init__(self, *args, **kwargs):
        self.selected_facets_or = kwargs.pop("selected_facets_or", [])
        self.sort_by = kwargs.pop("sort_by",None)
        super(ProductSearchForm, self).__init__(*args, **kwargs)

    category = forms.CharField(required=False)
    minPrice = forms.CharField(required=False)
    maxPrice = forms.CharField(required=False)

    def search(self):
        sqs = super(ProductSearchForm, self).search()

        if self.cleaned_data['category']:
                sqs = sqs.filter(category__exact=self.cleaned_data['category'])

        if self.cleaned_data['minPrice']:
                sqs = sqs.filter(price__gte=long(self.cleaned_data['minPrice']))

        if self.cleaned_data['maxPrice']:
                sqs = sqs.filter(price__lte=long(self.cleaned_data['maxPrice']))

        if self.sort_by:
                sqs = sqs.order_by(self.sort_by)

        or_facets = {}
        for facet in self.selected_facets_or:
            if ":" not in facet:
                continue

            field, value = facet.split(":", 1)

            if value:
                or_facets.setdefault(field,[]).append(value)

        for field, or_values in or_facets.items():
            or_narrow_query = " OR ".join(map(lambda i: u'%s:"%s"' % (field, sqs.query.clean(i)), or_values))
            sqs = sqs.narrow(or_narrow_query)

        return sqs