import re

from django.shortcuts import redirect

EXEMPT_URLS = [re.compile(url) for url in [r'/login/$', r'/static/*', r'/orders/shopify/callback/$']]


class AuthRequiredMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        exempt_url = any(m.match(request.path) for m in EXEMPT_URLS)
        if (not request.user.is_authenticated or not getattr(request.user, 'administrator', False)) and not exempt_url:
            return redirect('login')
        return response
