from django.db import models


# Create your models here.
from django.db import models
from jsonfield import JSONField
from jose import jwt
from django.conf import settings
from jsonLookup import shasLookup
JSONField.register_lookup(shasLookup)
