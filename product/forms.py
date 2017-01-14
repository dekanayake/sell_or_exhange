from django import forms
from .models import Product
from .models import ProductAttribute
from .models import SelectProductAttributeValues
from .models import ProductDataSelectValue
from .models import Brand
from .models import ProductData
from .models import Profile
from .models import SingleUser
from .models import Shop
from .models import Location
from django_summernote.widgets import SummernoteWidget
import logging
from django.utils.safestring import mark_safe
from haystack.forms import FacetedSearchForm
from haystack.utils.geo import Point, D
from django.core.files.base import ContentFile
from django.contrib.auth.models import User





class ProductForm(forms.ModelForm):

    featureElements =  {}
    choiceElements = []
    radioElements = []
    additionalAttributes = []
    productInstance = None


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
        if 'instance' in kwargs:
            self.productInstance = kwargs.pop('instance')
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


        if self.productInstance:
            self.__load_values_for_additional_attributes(self.productInstance)


    def __load_values_for_additional_attributes(self, productInstance):
        loadedProductDataList = ProductData.objects.filter(product__pk=productInstance.id)
        for loadedProductData in loadedProductDataList:
            if loadedProductData.productAttribute.type in ['RADIO','SELECT','CHECKBOX']:
                logging.warn ('''''''''''''''''''''''''''''''''''''''''''''''')
                logging.warn([ str(productDataSelectValue.selectValue.id) for productDataSelectValue in ProductDataSelectValue.objects.filter(productData__pk=loadedProductData.id)])
                self.initial[loadedProductData.productAttribute.name] =  [ str(productDataSelectValue.selectValue.id) for productDataSelectValue in ProductDataSelectValue.objects.filter(productData__pk=loadedProductData.id)]
            else:
                self.initial[loadedProductData.productAttribute.name] = loadedProductData.value



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

class ProfileForm(forms.Form):
    type = forms.ChoiceField(choices=Profile.PROFILE_TYPE)
    user_name = forms.CharField(label='User Name',max_length=500)
    email = forms.CharField(label='Email',max_length=500)
    password1 = forms.CharField(label="Password", max_length=100,widget=forms.PasswordInput)
    password2 = forms.CharField(label="Retype password", max_length=100,widget=forms.PasswordInput)
    image = forms.ImageField(required=False, label="Image")
    contact_number = forms.CharField(required=False, label="Contact Number")
    shop_name = forms.CharField(required=False, label="Shop name")
    shop_address1 = forms.CharField(required=False, label="Address 1")
    shop_address2 = forms.CharField(required=False, label="Address 2")
    shop_location = forms.ChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        locations = tuple((location.id, location.name) for location in Location.objects.exclude(parentLocation__isnull=True))
        self.fields['shop_location'].choices = locations

    def clean(self):
        cleaned_data = super(ProfileForm, self).clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 != password2:
            self.add_error('password1', 'Passwords are not matching')
            self.add_error('password2', 'Passwords are not matching, Please type the same password')

        type = cleaned_data.get("type")
        shop_location = cleaned_data.get("shop_location")
        logging.warning('shop_location')
        logging.warning(shop_location)
        logging.warning(type)

        if (type == "SHOP"):
            if not shop_location :
                self.add_error('shop_location', 'Please provide the city of the shop location')

        return cleaned_data

    def save(self,request):
        cleaned_data = super(ProfileForm, self).clean()
        profile =  Profile()
        profile.type = cleaned_data.get("type")
        profile.contactNumber = cleaned_data.get("contact_number")

        user = User()
        user.username = cleaned_data.get("user_name")
        user.email = cleaned_data.get("email")
        user.password = cleaned_data.get("password1")

        image = cleaned_data.get('image')
        if image:
            profile.image.save(image.name,ContentFile(image.read()), save=True )


        user.save()
        profile.save()



class ProductSearchForm(FacetedSearchForm):

    def __init__(self, *args, **kwargs):
        self.selected_facets_or = kwargs.pop("selected_facets_or", [])
        self.sort_by = kwargs.pop("sort_by",None)
        self.search_around = kwargs.pop('search_around',None)
        super(ProductSearchForm, self).__init__(*args, **kwargs)

    category = forms.CharField(required=False)
    location = forms.CharField(required=False)
    minPrice = forms.CharField(required=False)
    maxPrice = forms.CharField(required=False)

    def search(self):
        sqs = super(ProductSearchForm, self).search()

        if self.cleaned_data['category']:
                sqs = sqs.filter(category__exact=self.cleaned_data['category'])

        if self.cleaned_data['location']:
                sqs = sqs.filter(location__exact=self.cleaned_data['location'])

        if self.cleaned_data['minPrice']:
                sqs = sqs.filter(price__gte=long(self.cleaned_data['minPrice']))

        if self.cleaned_data['maxPrice']:
                sqs = sqs.filter(price__lte=long(self.cleaned_data['maxPrice']))

        if self.sort_by:
                sqs = sqs.order_by(self.sort_by)

        if (self.search_around):
                user_location = Point(self.search_around[0],self.search_around[1])
                max_dist = D(mi=35)
                sqs =  sqs.dwithin('geoLocation', user_location, max_dist)






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