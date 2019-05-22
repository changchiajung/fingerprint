from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, render_to_response,redirect
from django.contrib.auth import authenticate, login,logout
from django.template import RequestContext
from django.conf import settings
from django.http import JsonResponse
import random,string
import webauthn

RP_ID = 'duosecurity.com'

def log_user_in(request,username):
    from django.contrib.auth.models import User
    user=User.objects.get(username=username)
    user.backend='django.contrib.auth.backends.ModelBackend'
    login(request, user)

    if "redirect" in request.POST:
        return redirect(request.POST["redirect"])
    else:
        return redirect(settings.BASE_URL)

def check(request):
    if request.method =="GET":
        if "mfa" in settings.INSTALLED_APPS and getattr(settings,"MFA_QUICKLOGIN",False) and request.COOKIES.get('base_username'):
            print("in get funct")
            username=request.COOKIES.get('base_username')
            from mfa.helpers import has_mfa
            res =  has_mfa(username = username,request=request,)
            if res: return res
        return render_to_response("login.html")
    if request.method=="POST":
        username = request.POST['username']
        password = request.POST['password']
        print(username)
        print(password)
        user = authenticate(username=username, password=password)
        err=""
        if user is not None:
            if user.is_active:
                if "mfa" in settings.INSTALLED_APPS:
                    from mfa.helpers import has_mfa
                    res =  has_mfa(request,username=username)
                    print(res)
                    if res:
                        print("aa") 
                        return res
                    print("aa") 
                    return log_user_in(request,username)
            else:
                err="This user is NOT activated yet."
        else:
            err="The username or the password is wrong."
        print("Error:", err)
        return render_to_response("login.html",{"err":err})
    else:
        print("a")
        return render_to_response("login.html")

def signOut(request):
    logout(request)
    return render_to_response("logout.html",context_instance=RequestContext(request))
def index(request):
    return render(request,"finger.html")

def webauthn_begin_activate(request):
    username = request.POST.get('register_username')
    display_name = request.POST.get('register_display_name')
    rp_name = "Duo Security"
    challenge = generate_challenge(32)
    ukey = generate_ukey()


    make_credential_options = webauthn.WebAuthnMakeCredentialOptions(
        challenge, rp_name, RP_ID, ukey, username, display_name,
        'https://chendin.com')
    print(make_credential_options.registration_dict)
    return JsonResponse(make_credential_options.registration_dict)
def generate_challenge(challenge_len):
    return ''.join([
        random.SystemRandom().choice(string.ascii_letters + string.digits)
        for i in range(challenge_len)
    ])
def generate_ukey():
    return generate_challenge(20)
