from SalsaVerde.stock.forms.documents import UpdateDocumentForm
from SalsaVerde.stock.models import Document

from ...common.views import AddModelView, DetailView, ModelListView, UpdateModelView


class DocumentsList(ModelListView):
    model = Document
    display_items = [
        'type',
        'date_created',
        'author',
    ]

    def get_queryset(self):
        return super().get_queryset().select_related('author')


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
