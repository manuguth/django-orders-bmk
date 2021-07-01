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
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth.decorators import login_required

from orders.views import(
    SuccessView,
    OrderWizard,
    render_pdf_view,
    order_overview_view,
    order_detail_view,
    internnal_order_view
   )

from accounts.views import (
    login_view,
    logout_view,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', OrderWizard.as_view()),
    path('bestellung/', OrderWizard.as_view()),
    path('success', SuccessView),
    path('download', render_pdf_view),
    path('orders/overview', order_overview_view),
    # path('orders/<int:id>', order_detail_view.as_view(), name="form_order"),
    # path('orders/test', order_detail_view.as_view(), name="form_order"),
    # path('form/4/', order_detail_view.as_view(), name='form_4'),
    path('orders/<int:id>', login_required(order_detail_view.as_view())),
    path('orders/internal', login_required(internnal_order_view.as_view())),
    path('download/<slug:order_hash>', render_pdf_view),
    path('login/', login_view),
    path('logout/', logout_view),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
