from django.urls import reverse

from SalsaVerde.common.views import AddModelView, DetailView, ModelListView, UpdateModelView
from SalsaVerde.stock.forms.users import UpdateUserForm
from SalsaVerde.stock.models import Document, User


class UserList(ModelListView):
    model = User
    display_items = [
        'email',
        'first_name',
        'last_name',
        'last_logged_in',
    ]


user_list = UserList.as_view()


class UserDetails(DetailView):
    model = User
    display_items = [
        'email',
        ('Name', 'name'),
        ('Address', 'address'),
        'last_logged_in',
    ]

    def extra_display_items(self):
        return [
            {
                'title': 'Authored Documents',
                'qs': Document.objects.request_qs(self.request).filter(author=self.object),
                'fields': [('Document', 'name'), 'date_created'],
            },
            {
                'title': 'Associated Documents',
                'qs': Document.objects.request_qs(self.request).filter(focus=self.object),
                'fields': [('Document', 'name'), 'date_created'],
                'add_url': reverse('documents-add') + f'?focus={self.object.pk}',
            },
        ]


user_details = UserDetails.as_view()


class UserAdd(AddModelView):
    form_class = UpdateUserForm
    model = User


user_add = UserAdd.as_view()


class UserEdit(UpdateModelView):
    form_class = UpdateUserForm
    model = User


user_edit = UserEdit.as_view()
