from django.shortcuts import render
from django.http import HttpResponse
from .models import Category
from .forms import ProductForm




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
        productForm =  ProductForm(category=category_id_long_value)
        return render(request, 'product/addProduct.html', {'selectedCategory':selectedCategory,'form':productForm})








