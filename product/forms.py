from django import forms
from .models import Product
from .models import ProductAttribute
from .models import SelectProductAttributeValues
from .models import Brand
from collections import defaultdict
import logging





class ProductForm(forms.ModelForm):

    featureElements =  {}
    choiceElements = []


    class Meta:
        model = Product
        fields = ['title','condition','description','price','negotiable','exchangeable','brand']

    def __init__(self, *args, **kwargs):
        self.featureElements = {}
        selectedCategory = kwargs.pop('category')
        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields['brand'].queryset = Brand.objects.filter(category__pk=long(selectedCategory))
        productAttributes = ProductAttribute.objects.filter(category__pk=long(selectedCategory))
        for productAttribute in productAttributes:

            group = productAttribute.group
            if group is None:
                group = 'EMPTY'

            self.featureElements.setdefault(str(group), []).append(productAttribute.name)

            if productAttribute.type == 'SELECT':
                selectValues = tuple((selectValue.name, selectValue.name) for selectValue in productAttribute.selectValues.all())
                self.fields[productAttribute.name] =  forms.ChoiceField(choices=selectValues)
            if productAttribute.type == 'CHECKBOX':
                self.fields[productAttribute.name] =  forms.BooleanField()
                self.choiceElements.append(productAttribute.name)











