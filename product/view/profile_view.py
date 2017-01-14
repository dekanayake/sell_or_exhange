from product.forms import ProfileForm
import base64
from django.views.generic.edit import FormView
import logging
import re
from product.models import Profile
from django.contrib.auth.models import User
from django.core.files.base import ContentFile


class ProfileView(FormView):
    form_class=ProfileForm
    template_name = 'profile/profile.html'
    success_url = '/thanks/close'



    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        type = self.request.GET.get('type')
        if type:
            context.update({'type':type})
            context.update({'type_url':ProfileView.__removeParamsFromURL(self.request.get_full_path(),['[?]type=.*'])})

        return context

    def form_valid(self, form):
        logging.warning('ha ha ----------------------------------------------------------------------------------')
        form.save(self.request)
        return super(ProfileView, self).form_valid(form)

    def form_invalid(self, form):
            logging.warning('ha ha -----------------------------------invalid-----------------------------------------------')
            return super(ProfileView, self).form_invalid(form)



    @staticmethod
    def __removeParamsFromURL(requestURL, regxToRemoveList):
        url = requestURL
        for regxPattern in regxToRemoveList:
            url = re.sub(regxPattern,'',url)
        return url