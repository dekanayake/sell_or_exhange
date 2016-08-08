from django.shortcuts import render_to_response, redirect
from django import template


register = template.Library()

@register.inclusion_tag('errors.html')
def errors(error_messages):
    return {'error_messages': error_messages}

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)