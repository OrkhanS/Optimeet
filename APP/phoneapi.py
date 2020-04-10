import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.throttling import UserRateThrottle
from rest_framework.permissions import AllowAny
from APP.models import User
from django.http import HttpResponse,JsonResponse
from django.shortcuts import render
from rest_framework import status
import json

class PhoneMinThrottle(UserRateThrottle):
    scope = 'phone_min'

class PhoneHourThrottle(UserRateThrottle):
    scope = 'phone_hour'

class PhoneDayThrottle(UserRateThrottle):
    scope = 'phone_day'

class Verify(APIView):
    def post(self, request):
        user=User.objects.get(id=request.user.id)
        if user.is_number_verified == request.data['verification_phone']:
            user.is_number_verified = "true"
            user.save()
            return Response({"detail":"Successfully verified"})
        else:
            return Response({"detail":"Uh-oh, Verification code isn't correct"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail":"Uh-oh, Something went wrong"}, status=status.HTTP_400_BAD_REQUEST)

class Request(APIView):
    throttle_classes = [
        PhoneMinThrottle,
        PhoneHourThrottle,
        PhoneDayThrottle
    ]

    def post(self, request):
        APIKEY = 'a09cb574b2af34b7be4b05d7e9255c4f'
        msisdn = request.data['phone']
        if msisdn == '':
            return_response = {
                'error': True,
                'info': 'Phone Number Cannot empty'
            }
            return JsonResponse(return_response)
        
        if 'trying' not in request.session:
            gateway = 0
            request.session['gateway'] = gateway
        else:
            gateway = request.session['gateway'] + 1
            if gateway > 4 :
                gateway = 0
            request.session['gateway'] = gateway

        base_url = "http://104.199.196.122/gateway"
        version = "/v3"
        action = "/asynccall"

        url = base_url + version + action
        data = {
            'msisdn':msisdn,
            'gateway':gateway
        }


        content = json.dumps(data)

        headers = {
            "Content-Type":"application/json",
            "Authorization": 'Apikey '+ APIKEY,
            "Content-Length":str(len(content))
        }

        r = requests.post(url,data=content,headers=headers)
        response_json = r.json()
        
        #print(verify_code) # debugging, you can comment this line
        
        rc = response_json['rc']
        error = True

        if rc == 0:
            user = User.objects.get(id=request.user.id)
            user.is_number_verified=response_json['token'][8:12]
            user.save()
            error = False
            token = response_json['token']
            trxid = response_json['trxid']
            request.session['token'] = token
            request.session['trxid'] = trxid
            first_token = token[0:-4]
            length = len(token)
            this_return = {
                'error':error,
                'trxid':trxid,
                'first_token':first_token,
                'length':length
            }
        else:
            info = response_json['info']
            this_return = {
                'error':error,
                'info':info
            }
            return Response(this_return, status=status.HTTP_400_BAD_REQUEST)

        #print(this_return) # debugging, you can comment this line
        return Response(this_return)
