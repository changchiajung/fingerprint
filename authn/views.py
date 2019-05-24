from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, render_to_response,redirect
from django.contrib.auth import authenticate, login,logout
from django.template import RequestContext
from django.conf import settings
from django.http import JsonResponse
import random,string
import webauthn.webauthn as webauthn
from .models import User_T
import os
import sys

RP_ID = 'localhost'
ORIGIN = 'https://localhost:8000'
TRUST_ANCHOR_DIR = 'trusted_attestation_roots'
session={}
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
                    if res:
                        return res
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
    challenge = generate_challenge(43)
    ukey = generate_ukey()
    if 'register_ukey' in session:
        del session['register_ukey']
    if 'register_username' in session:
        del session['register_username']
    if 'register_display_name' in session:
        del session['register_display_name']
    if 'challenge' in session:
        del session['challenge']
    session['register_username'] = username
    session['register_display_name'] = display_name
    session['challenge'] = challenge
    session['register_ukey'] = ukey

    make_credential_options = webauthn.WebAuthnMakeCredentialOptions(
        challenge, rp_name, RP_ID, ukey, username, display_name,
        'https://chendin.com')
    print(make_credential_options.registration_dict)
    temp = make_credential_options.registration_dict
    temp['attestation']='indirect'
    return JsonResponse(temp)


def webauthn_begin_assertion(request):
    username = request.POST.get('register_username')
    challenge = generate_challenge(32)
    user = User_T.objects.get(username=username)
    webauthn_user = webauthn.WebAuthnUser(
        user.ukey, user.username, user.display_name, user.icon_url,
        user.credential_id, user.pub_key, user.sign_count, user.rp_id)

    webauthn_assertion_options = webauthn.WebAuthnAssertionOptions(
        webauthn_user, challenge)
    return JsonResponse(webauthn_assertion_options.assertion_dict)

def verify_credential_info(request):
    challenge = session['challenge']
    username = session['register_username']
    display_name = session['register_display_name']
    ukey = session['register_ukey']
    registration_response = request.form
    trust_anchor_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), TRUST_ANCHOR_DIR)
    trusted_attestation_cert_required = True
    self_attestation_permitted = True
    none_attestation_permitted = True
    webauthn_registration_response = webauthn.WebAuthnRegistrationResponse(
        RP_ID,
        ORIGIN,
        registration_response,
        challenge,
        trust_anchor_dir,
        trusted_attestation_cert_required,
        self_attestation_permitted,
        none_attestation_permitted,
        uv_required=False)
    try:
        webauthn_credential = webauthn_registration_response.verify()
    except Exception as e:
        return JsonResponse({'fail': 'Registration failed. Error: {}'.format(e)})

    credential_id_exists = User_T.get(
        credential_id=webauthn_credential.credential_id)
    if credential_id_exists:
        return JsonResponse({ 'fail': 'Credential ID already exists.'})

    existing_user = User_T.get(username=username)
    if not existing_user:
        if sys.version_info >= (3, 0):
            webauthn_credential.credential_id = str(
                webauthn_credential.credential_id, "utf-8")
        user = User_T.objects.create(
            ukey=ukey,
            username=username,
            display_name=display_name,
            pub_key=webauthn_credential.public_key,
            credential_id=webauthn_credential.credential_id,
            sign_count=webauthn_credential.sign_count,
            rp_id=RP_ID,
            icon_url='https://example.com')
    else:
        return JsonResponse({'fail': 'User already exists.'})
    print('Successfully registered as {}.'.format(username))
    return JsonResponse({'success': 'User successfully registered.'})

def verify_assertion(request):
    challenge = session['challenge']
    assertion_response = request.form
    credential_id = assertion_response.get('id')

    user = User_T.get(credential_id=credential_id)
    if not user:
        return JsonResponse({'fail': 'User does not exist.'})

    webauthn_user = webauthn.WebAuthnUser(
        user.ukey, user.username, user.display_name, user.icon_url,
        user.credential_id, user.pub_key, user.sign_count, user.rp_id)

    webauthn_assertion_response = webauthn.WebAuthnAssertionResponse(
        webauthn_user,
        assertion_response,
        challenge,
        ORIGIN,
        uv_required=False)  # User Verification

    try:
        sign_count = webauthn_assertion_response.verify()
    except Exception as e:
        return JsonResponse({'fail': 'Assertion failed. Error: {}'.format(e)})

    # Update counter.
    user.sign_count +=1
    user.save()

    login(request,user)

    return JsonResponse({
        'success':
        'Successfully authenticated as {}'.format(user.username)
    })

def logout():
    logout()
    return redirect('../index')



def generate_challenge(challenge_len):
    return ''.join([
        random.SystemRandom().choice(string.ascii_letters + string.digits)
        for i in range(challenge_len)
    ])
def generate_ukey():
    return generate_challenge(20)
