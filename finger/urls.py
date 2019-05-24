"""finger URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import include, url
#import mfa.TrustDevice
import mfa
import mfa
from authn.views import check,index,webauthn_begin_activate,webauthn_begin_assertion,verify_credential_info
from . import FIDO2
urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^mfa/', include('mfa.urls')),
    url(r'devices/add$', mfa.TrustedDevice.add,name="mfa_add_new_trusted_device"),
    path("index/",check),
    path("index/login",check),
    path("finger",index),
    path("webauthn_begin_activate",webauthn_begin_activate),
    path("webauthn_begin_assertion",webauthn_begin_assertion),
    path("verify_credential_info",verify_credential_info),
    path("verify_credential_info",check),
    url(r'fido2/$', FIDO2.start, name="start_fido2"),
    url(r'fido2/auth', FIDO2.auth, name="fido2_auth"),
    url(r'fido2/begin_auth', FIDO2.authenticate_begin, name="fido2_begin_auth"),
    url(r'fido2/complete_auth', FIDO2.authenticate_complete, name="fido2_complete_auth"),
    url(r'fido2/begin_reg', FIDO2.begin_registeration, name="fido2_begin_reg"),
    url(r'fido2/complete_reg', FIDO2.complete_reg, name="fido2_complete_reg"),
]
