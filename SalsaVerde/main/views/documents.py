from .base_views import ListView, DetailView, AddModelView, UpdateModelView
from SalsaVerde.main.forms import UpdateDocumentForm
from SalsaVerde.main.models import Document


class DocumentsList(ListView):
    model = Document
    display_items = [
        'type',
        'date_created',
        'author',
    ]


document_list = DocumentsList.as_view()


class DocumentDetails(DetailView):
    model = Document
    display_items = [
        'type',
        'date_created',
        'author',
        'file',
        'supplier',
        'focus',
    ]


document_details = DocumentDetails.as_view()


class DocumentAdd(AddModelView):
    model = Document
    form_class = UpdateDocumentForm


document_add = DocumentAdd.as_view()


class DocumentEdit(UpdateModelView):
    model = Document
    form_class = UpdateDocumentForm


document_edit = DocumentEdit.as_view()
