from django import forms
from .models import Product
from .models import ProductAttribute
from .models import SelectProductAttributeValues
from .models import Brand
from .models import ProductData
from django_summernote.widgets import SummernoteWidget
import logging





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
                selectValues = tuple((selectValue.name, selectValue.name) for selectValue in productAttribute.selectValues.all())
                self.fields[productAttribute.name] =  forms.ChoiceField(choices=selectValues,required=productAttribute.required)
            if productAttribute.type == 'CHECKBOX':
                selectValues = tuple((selectValue.name, selectValue.name) for selectValue in productAttribute.selectValues.all())
                self.fields[productAttribute.name] =  forms.MultipleChoiceField(choices=selectValues,required=productAttribute.required)
                self.choiceElements.append(productAttribute.name)
            if productAttribute.type == 'RADIO':
                selectValues = tuple((selectValue.name, selectValue.name) for selectValue in productAttribute.selectValues.all())
                self.fields[productAttribute.name] =  forms.ChoiceField(choices=selectValues,required=productAttribute.required)
                self.radioElements.append(productAttribute.name)
            if productAttribute.type == 'TEXT':
                selectValues = tuple((selectValue.name, selectValue.name) for selectValue in productAttribute.selectValues.all())
                self.fields[productAttribute.name] =  forms.CharField(required=productAttribute.required)
            if productAttribute.type == 'NUMBER':
                selectValues = tuple((selectValue.name, selectValue.name) for selectValue in productAttribute.selectValues.all())
                self.fields[productAttribute.name] =  forms.IntegerField(required=productAttribute.required)





    def get_product_data_list(self):
            productDataList = []
            for productAttribute in self.additionalAttributes:
                elementValue = self.cleaned_data[productAttribute.name]
                if productAttribute.type == 'CHECKBOX':
                    elementValue = ','.join(elementValue)
                productData = ProductData()
                productData.value = elementValue
                productData.productAttribute = productAttribute
                productDataList.append(productData)
            return productDataList




