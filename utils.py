from kavenegar import *
from dotenv import load_dotenv
import os

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