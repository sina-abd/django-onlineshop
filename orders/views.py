from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from .cart import Cart
from home.models import Product
from .forms import CartAddForm, CouponApplyForm
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Order, OrderItem, Coupon
from django.conf import settings
from dotenv import load_dotenv
import os
import json
import requests
import datetime
from django.contrib import messages


class CartView(View):
    def get(self, requset):
        cart = Cart(requset)
        return render(requset, 'orders/cart.html', {'cart':cart})

class CartAddView(View):
    def post(self, request, product_id):
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id)
        form = CartAddForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            cart.add(product, cd['quantity'])
        return redirect('orders:cart')
    
class CartRemoveView(View):
    def get(self, request, product_id):
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id)
        cart.remove(product)
        return redirect('orders:cart')
    
class OrderDetailView(LoginRequiredMixin, View):
    form_class = CouponApplyForm

    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        return render(request, 'orders/order.html', {'order':order, 'form':self.form_class})
    
class OrderCreateView(LoginRequiredMixin, View):
    def get(self, request):
        cart = Cart(request)
        order = Order.objects.create(user=request.user)
        for item in cart:
            OrderItem.objects.create(order=order, product=item['product'], price=item['price'], quantity=item['quantity'])
        cart.clear()
        return redirect('orders:order_detail', order.id)
    
description = "توضیحات مربوط به تراکنش را در این قسمت وارد کنید"
CallbackURL = 'http://127.0.0.1:8080/orders/verify/'
    
class OrderPayView(LoginRequiredMixin, View):
    def get(self, request, order_id):
        order = Order.objects.get(id=order_id)
        request.session['order_pay'] = {
            'order_id': order_id
        }
        load_dotenv()
        data = {
        "MerchantID": os.get_env('MERCHANT'),
        "Amount": order.get_total_price(),
        "Description": description,
        "Phone": request.user.phone_number,
        "CallbackURL": CallbackURL,
    }
        data = json.dumps(data)
        headers = {'content-type': 'application/json', 'content-length': str(len(data)) }
        try:
            response = requests.post(os.getenv("ZP_API_REQUEST"), data=data,headers=headers, timeout=10)

            if response.status_code == 200:
                response = response.json()
                if response['Status'] == 100:
                    return {'status': True, 'url': os.getenv("ZP_API_REQUEST") + str(response['Authority']), 'authority': response['Authority']}
                else:
                    return {'status': False, 'code': str(response['Status'])}
            return response
        except requests.exceptions.Timeout:
            return {'status': False, 'code': 'timeout'}
        except requests.exceptions.ConnectionError:
            return {'status': False, 'code': 'connection error'}

class OrderVerifyView(LoginRequiredMixin ,View):
    def get(self, request):
        order_id = request.session['order_pay']['order_id']
        order = Order.objects.get(id=int(order_id))
        data = {
        "MerchantID": os.getenv("MERCHANT"),
        "Amount": order.get_total_price,
        "Authority": request.GET['authority'],
        }
        data = json.dumps(data)
        headers = {'content-type': 'application/json', 'content-length': str(len(data)) }
        response = requests.post(os.getenv("ZP_API_VERIFY"), data=data,headers=headers)

        if response.status_code == 200:
            response = response.json()
            if response['Status'] == 100:
                order.paid = True
                order.save()
                return {'status': True, 'RefID': response['RefID']}
            
            else:
                return {'status': False, 'code': str(response['Status'])}
        return response
    
class CouponApplyView(LoginRequiredMixin, View):
    form_class = CouponApplyForm
    def post(self, request, order_id):
        now = datetime.datetime.now()
        form = self.form_class(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            try:
                coupon = Coupon.objects.get(code__exact=code, valid_from__lte=now, valid_to__gte=now, is_active=True)
            except Coupon.DoesNotExist:
                messages.error(request, 'this coupon does not exist', 'danger')
                return redirect('orders:order_detail', order_id)
            order = Order.objects.get(id=order_id)
            order.discount = coupon.discount
            order.save()
        return redirect('orders:order_detail', order_id)