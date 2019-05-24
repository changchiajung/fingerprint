from django.db import models


# Create your models here.


class User_T(models.Model):
    id = models.IntegerField(blank=True,primary_key=True)
    ukey = models.CharField(max_length=20,blank=True)
    credential_id = models.CharField(max_length=250,blank=True)
    display_name = models.CharField(max_length=160,blank=True)
    pub_key = models.CharField(max_length=65,blank=True)
    sign_count = models.IntegerField(blank=True)
    username = models.CharField(max_length=80,blank=True)
    rp_id = models.CharField(max_length=253,blank=True)
    icon_url = models.CharField(max_length=2083,blank=True)

    def __repr__(self):
        return '<User %r %r>' % (self.display_name, self.username)