from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError


class AuthForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.administrator:
            raise ValidationError(self.error_messages['inactive'], code='inactive')
