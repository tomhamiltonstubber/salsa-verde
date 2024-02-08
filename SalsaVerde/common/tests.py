from django.test import TestCase


class SVTestCase(TestCase):
    def assertRedirects(self, response, *args, **kwargs):
        try:
            super().assertRedirects(response, *args, **kwargs)
        except AssertionError:
            if response.status_code == 200 and response.context and 'form' in response.context:
                errors = response.context['form'].errors
                if errors:
                    raise AssertionError(f"Response didn't redirect because of form errors:\n{errors.get_json_data()}")
            raise
