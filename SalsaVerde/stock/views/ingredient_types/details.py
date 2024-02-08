from SalsaVerde.common.views import DetailView
from SalsaVerde.stock.models import IngredientType


class IngredientTypeDetails(DetailView):
    model = IngredientType
    display_items = ['name', 'unit']

    def extra_display_items(self):
        return [
            {
                'title': 'Ingredients',
                'qs': self.object.ingredients.select_related('ingredient_type').order_by('-intake_date'),
                'fields': ['ingredient_type', 'batch_code', ('Intake date', 'intake_date'), 'supplier'],
            }
        ]


ingredient_type_details = IngredientTypeDetails.as_view()
