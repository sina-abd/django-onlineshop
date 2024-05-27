from kavenegar import *
from dotenv import load_dotenv
import os
from django.contrib.auth.mixins import UserPassesTestMixin

def send_OTPcode(phone_number, code):

    load_dotenv()
    try:
        api = KavenegarAPI(os.getenv('API_KEY'))
        params = {
            'sender':'',
            'receptor': phone_number,
            'message': f'کد تایید شما {code}'
        }
        response = api.sms_send(params)
    except APIException as e:
        print(e)
    except HTTPException as e:
        print(e)

class IsAdminUserMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin