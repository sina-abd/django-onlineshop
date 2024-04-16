from django.shortcuts import render, redirect
from django.views import View
from .forms import UserRegistrarionForm, VerificationCodeForm
import random
from utils import send_OTPcode
from .models import OTPCode, User
from django.contrib import messages
from datetime import datetime, timedelta


class UserRegisterView(View):

    form_class = UserRegistrarionForm

    def get(self, request):
        form = self.form_class
        return render(request, 'accounts/register.html', {'form':form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            random_code = random.randint(1000, 9999)
            send_OTPcode(form.cleaned_data['phone_number'], random_code)
            OTPCode.objects.create(phone_number=form.cleaned_data['phone_number'], code=random_code)
            request.session['user_registration_info'] = {
                'phone_number': form.cleaned_data['phone_number'],
                'email': form.cleaned_data['email'],
                'full_name': form.cleaned_data['full_name'],
                'password': form.cleaned_data['password'],
            }
            messages.success(request, 'We sent you a code', 'success')
            return redirect('accounts:user_verification')
        return render(request, 'accounts/register.html', {'form':form})
    
class UserVerificationView(View):

    form_class = VerificationCodeForm

    def get(self, request):
        form = self.form_class
        return render(request, 'accounts/verification.html', {'form':form})

    def post(self,request):
        user_session = request.session['user_registration_info']
        code_instance = OTPCode.objects.get(phone_number=user_session['phone_number'])
        form = self.form_class(request.POST)
        code_now_difference = (datetime.now() - code_instance.created).total_seconds() 
        print('#'*150)
        print(type(code_instance.created))
        print(type(datetime.now()))
        if form.is_valid():
            cd = form.cleaned_data
            if cd['code'] == code_instance.code:
                if code_now_difference <= 120: #solve this
                    User.objects.create_user(user_session['phone_number'], user_session['email'], 
                                            user_session['full_name'], user_session['password'])
                    code_instance.delete()
                    messages.success(request, 'you verified succussfully', 'success')
                    return redirect('home:home')
                else:
                    messages.error(request, 'The code time is over', 'danger')
                    return redirect('accounts:user_verification')
            else:
                messages.error(request, 'The code is wrong', 'danger')
                return redirect('accounts:user_verification')
        return redirect('home:home')

