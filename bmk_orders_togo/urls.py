"""bmk_orders_togo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from orders.forms import OrderModelForm, OrderProductForm, OrderTimeSlotForm

from orders.views import(
    SuccessView,
    OrderWizard,
    )

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('personal_details/', CrispyAddressFormView, name='personal_details'),
    # path('order/', OrderProductView, name='order'),
    # path('personal_details/',
    #      CrispyAddressFormView.as_view(
    #          template_name='orders/personal_details.html'),
    #      name='form_2'),
    path('bestellung/', OrderWizard.as_view()),
    # path('time_slot/', OrderTimeSlotView, name='time_slot'),
    path('success/', SuccessView.as_view(), name='success'),
]
