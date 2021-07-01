from django.contrib.auth import authenticate, login
import os
import secrets
from django.db import connection
from django.shortcuts import render, redirect

from django.http import HttpResponseRedirect
from formtools.wizard.views import SessionWizardView
from django.core.mail import EmailMessage
from django.core import mail

from django.contrib.auth.decorators import login_required

from django.views.generic import FormView, TemplateView
from django.urls import reverse_lazy

from .forms import(
    OrderModelForm,
    OrderProductForm,
    OrderTimeSlotForm,
    OrderCheckoutForm,
    OrderProductEditForm,
    OrderProductInternalForm,
    )
from .models import Order

from products.models import Product
from inventory.models import Inventory

from django.utils import timezone
from django.utils.dateparse import parse_datetime
import locale

import os
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib.staticfiles import finders

from django.template.loader import render_to_string
from io import BytesIO
from tempfile import TemporaryFile

if 'WEBSITE_HOSTNAME' not in os.environ:
    locale.setlocale(locale.LC_ALL, 'de_DE')
elif 'WEBSITE_HOSTNAME' in os.environ:
    locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')



FORMS = [("productchoice", OrderProductForm),
         ("timeslot", OrderTimeSlotForm),
         ("personaldetails", OrderModelForm),
         ("confirmation", OrderCheckoutForm)]

TEMPLATES = {"productchoice": "orders/formtools.html",
             "timeslot": "orders/formtools-timeslot.html",
             "personaldetails": "orders/formtools-contact-form.html",
             "confirmation": "orders/confirmation_formtools.html"}


def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those
    resources
    """
    result = finders.find(uri)
    if result:
            if not isinstance(result, (list, tuple)):
                    result = [result]
            result = list(os.path.realpath(path) for path in result)
            path = result[0]
    else:
            sUrl = settings.STATIC_URL        # Typically /static/
            sRoot = settings.STATIC_ROOT      # Typically /home/userX/project_static/
            mUrl = settings.MEDIA_URL         # Typically /media/
            mRoot = settings.MEDIA_ROOT       # Typically /home/userX/project_static/media/

            if uri.startswith(mUrl):
                    path = os.path.join(mRoot, uri.replace(mUrl, ""))
            elif uri.startswith(sUrl):
                    path = os.path.join(sRoot, uri.replace(sUrl, ""))
            else:
                    return uri

    # make sure that file exists
    if not os.path.isfile(path):
            raise Exception(
                'media URI must start with %s or %s' % (sUrl, mUrl)
            )
    return path


def render_pdf_view(request, order_hash):
    template_path = 'orders/invoice-new.html'
    # fP4QYKCW1tNr3hWN-zjA5g
    order = Order.objects.get(order_hash=order_hash)
    class_date = timezone.localtime(order.time_slot)
    context = {
        'myvar': 'this is your template context',
        'date': timezone.now().strftime("%d.%m.%Y"),
        'namebesteller': order.name,
        'mail': order.email,
        'phone': order.phone,
        'bestellid': order.id,
        'abholdatum': class_date.strftime("%A %d. %B"),
        'abholzeit': class_date.strftime("%H:%M"),
        'products': getproductoverview(order.ordered_products),
        'total': calculateprice(order.ordered_products),
        'comments': order.comments
        
        }
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Bestellbestätigung-{context["bestellid"]}.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)
    

    # create a pdf
    pisa_status = pisa.CreatePDF(
        html, dest=response, link_callback=link_callback)
    
    file = TemporaryFile(mode="w+b")
    pisa.CreatePDF(html, dest=file, link_callback=link_callback)

    file.seek(0)
    pdf = file.read()
    file.close()
    # email = EmailMessage(
    #     'Hello', 'Body', 'bestellung@bmk-buggingen.de', ['bestellung@bmk-buggingen.de'])
    # email.attach(f"Bestellbestätigung-{order.id}.pdf", pdf, 'application/pdf')
    # email.send()
    # store to db
    # order_i = Order.objects.get(order_hash="fP4QYKCW1tNr3hWN-zjA5g")
    # order_i.invoice = pdf # seems not to work ...
    # order_i.save()
    
    # if error then show some funny view
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    # purch_upd = purchase.objects.get(pk=purch_id)
    # purch_upd.receipt = File(receipt_file, filename)
    return response


def GetPDFOrderContext(order):
    class_date = timezone.localtime(order.time_slot)
    context = {
        'date': timezone.now().strftime("%d.%m.%Y"),
        'namebesteller': order.name,
        'mail': order.email,
        'phone': order.phone,
        'bestellid': order.id,
        'abholdatum': class_date.strftime("%A %d. %B"),
        'abholzeit': class_date.strftime("%H:%M"),
        'products': getproductoverview(order.ordered_products),
        'total': calculateprice(order.ordered_products),
        'comments': order.comments
    }
    return context

def get_pdf(order):
    template = get_template('orders/invoice-new.html')
    html = template.render(GetPDFOrderContext(order))
    file = TemporaryFile(mode="w+b")
    pisa.CreatePDF(html, dest=file, link_callback=link_callback)
    file.seek(0)
    pdf = file.read()
    file.close()
    return pdf

def calculateprice(form_product_data, n_products=False):
    price = 0
    products = 0
    for item in form_product_data:
        if form_product_data[item] is None:
            continue
        price += form_product_data[item] * Product.objects.get(short_title=item).price
        products += form_product_data[item]
    
    if n_products:
        return price, products
    return price


def getproductoverview(form_product_data):
    products = []
    for item in form_product_data:
        if form_product_data[item] is None or form_product_data[item] == 0:
            continue
        product = {}
        obj = Product.objects.get(short_title=item)
        product["name"] = obj.title
        product["amount"] = form_product_data[item]
        product["price"] = obj.price
        product["total"] = form_product_data[item] * obj.price
        products.append(product)
    return products
    

def sendmail(mailto, name, price, timeslot, order_id, connection,
             custom_message=None):
    message = f"""
Guten Tag {name}, 

vielen Dank für Ihre Bestellung. Anbei erhalten Sie Ihre Bestellbestätigung als pdf-Datei.

Bitte bezahlen Sie den fälligen Betrag von {price} € bei Abholung Ihrer Bestellung am {timeslot} passend in bar.

Bei Rückfragen stehen wir Ihnen gerne zur Verfügung unter bestellung@bmk-buggingen.de.

Ihre Bergmannskapelle Buggingen e.V.
"""
    if custom_message is not None:
        message = custom_message
    email = EmailMessage(
        subject=f'Bestellbestätigung Festessen To Go - Bestellung {order_id}',
        body=message,
        from_email='"Bestellung BMK Buggingen"<bestellung@bmk-buggingen.de>',
        to=[mailto],
        bcc=['bestellung@bmk-buggingen.de'],
        connection=connection
        # reply_to=['another@example.com'],
        # headers={'Message-ID': 'foo'},
    )
    return email


class OrderWizard(SessionWizardView):
    form_list = FORMS
    def get_template_names(self):
        return [TEMPLATES[self.steps.current]]

    def get_context_data(self, form, ** kwargs):
        context = super().get_context_data(form=form, **kwargs)
        if self.steps.current == 'confirmation':
            price = calculateprice(
                super().get_cleaned_data_for_step("productchoice")
                )
            products = getproductoverview(
                super().get_cleaned_data_for_step("productchoice"))
            class_date = timezone.localtime(
                parse_datetime(super().get_cleaned_data_for_step("timeslot")["time_slot"]))
            timeslot = class_date.strftime("%A %d. %B %H:%M")
            context.update(
                {'price': price, "products": products, "timeslot": timeslot})
        # if self.steps.current == 'timeslot':
        #     price = calculateprice(
        #         super().get_cleaned_data_for_step("productchoice"),
        #         n_products=True
        #         )
            # TODO: find a way to check which timeslot is still available
        return context
    
    def done(self, form_list, **kwargs):
        # print(form_list[0].cleaned_data)
        # print([form.cleaned_data for form in form_list])
        personal_details = super().get_cleaned_data_for_step("personaldetails")
        products = super().get_cleaned_data_for_step("productchoice")
        price, n_ordered_products = calculateprice(products, n_products=True)
        class_date = timezone.localtime(
            parse_datetime(super().get_cleaned_data_for_step("timeslot")["time_slot"]))
        timeslot = class_date.strftime("%A %d. %B %H:%M")
        
        # create a unique hash for each order
        order_hash = secrets.token_urlsafe(16)

        order = Order(
            time_stamp=timezone.now(),
            name=personal_details["name"],
            email=personal_details["email"],
            phone=personal_details["phone"],
            comments=personal_details["comments"],
            time_slot=class_date,
            price_total=price,
            ordered_products=products,
            order_hash=order_hash,
            n_ordered_products=n_ordered_products,
        )
        order.save()
        # retrieve order ID and set variable
        order_id = order.id
        # augmenting amount of ordered food
        # TODO: do something more sophisticated here???
        # need a function which looks up all orders, maybe only for a later stage this implementation looks good for here now
        # needed when updating an order manually
        timeslot_db = Inventory.objects.get(time_slot=class_date)
        timeslot_db.received_orders += n_ordered_products
        timeslot_db.save()
        # TODO: check again if timeslot matches ordered food - probably not necessary
        pdf = get_pdf(order)
        
        with mail.get_connection() as connection:
            email = sendmail(mailto=personal_details["email"],
                             name=personal_details["name"],
                            price=price,
                            timeslot=timeslot,
                             order_id=order_id,
                            connection=connection)
            email.attach(
                f"Bestellbestätigung-{order.id}.pdf", pdf, 'application/pdf')
            email.send()
        return render(self.request, 'orders/success.html', {
            'form_data': [form.cleaned_data for form in form_list],
            'order_id': order_id, "order_hash": order_hash
        })
    

# class SuccessView(TemplateView):
#     template_name = 'orders/success.html'

def SuccessView(request):
    return render(request, "orders/success.html")


# @login_required
class order_detail_view(FormView):
    form_class = OrderProductEditForm
    success_url = reverse_lazy('orders/success.html')
    template_name = 'orders/crispy_form.html'



@login_required
def order_overview_view(request):
    """"""
    orders = Order.objects.all()
    return render(request, "orders/overview.html", 
                  {'orders': orders})


class order_detail_view(FormView):
    form_class = OrderProductEditForm
    success_url = '/orders/overview'
    template_name = 'orders/crispy_form.html'
    # TODO: seems not to work yet, need to figure out how to pass context data
    context_object_name = 'order'

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        qs = Product.objects.all()
        fields = [[i.short_title, i.display_order, i.id] for i in qs]
        fields = sorted(fields, key=lambda l: l[1])
        field_names = [i[0] for i in fields]
        form_data = form.cleaned_data
        products = {
            your_key: form_data[your_key] for your_key in field_names}
        ordered_products = form_data
        class_date = timezone.localtime(parse_datetime(form_data["time_slot"]))
        price, n_ordered_products = calculateprice(products, n_products=True)
        order = Order.objects.get(id=self.id)
        order.name = form_data["name"]
        order.email = form_data["email"]
        order.phone = form_data["phone"]
        order.comments = form_data["comments"]
        order.time_slot = class_date
        order.price_total = price
        order.ordered_products = products
        order.n_ordered_products = n_ordered_products
        order.save()
        UpdateInventory()
        if form_data["send_mail"]:
            pdf = get_pdf(order)
            timeslot = class_date.strftime("%A %d. %B %H:%M")

            with mail.get_connection() as connection:
                email = sendmail(mailto=form_data["email"],
                                 name=form_data["name"],
                                price=price,
                                 timeslot=timeslot,
                                 order_id=order.id,
                                connection=connection,
                                 custom_message=form_data["mailtext"])
                email.attach(
                    f"Bestellbestätigung-{order.id}.pdf", pdf, 'application/pdf')
                email.send()
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super(order_detail_view, self).get_form_kwargs()
        kwargs['id'] = self.kwargs['id']
        self.id = self.kwargs['id']
        return kwargs
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['price'] = 12
        return context


class internnal_order_view(FormView):
    form_class = OrderProductInternalForm
    success_url = '/orders/overview'
    template_name = 'orders/crispy_form.html'
    # TODO: seems not to work yet, need to figure out how to pass context data
    context_object_name = 'order'

    def form_valid(self, form):
        qs = Product.objects.all()
        fields = [[i.short_title, i.display_order, i.id] for i in qs]
        fields = sorted(fields, key=lambda l: l[1])
        field_names = [i[0] for i in fields]
        form_data = form.cleaned_data
        products = {
            your_key: form_data[your_key] for your_key in field_names}
        ordered_products = form_data
        class_date = timezone.localtime(parse_datetime(form_data["time_slot"]))
        price, n_ordered_products = calculateprice(products, n_products=True)
        
        # create a unique hash for each order
        order_hash = secrets.token_urlsafe(16)

        order = Order(
            time_stamp=timezone.now(),
            name=form_data["name"],
            email=form_data["email"],
            phone=form_data["phone"],
            comments=form_data["comments"],
            time_slot=class_date,
            price_total=price,
            ordered_products=products,
            order_hash=order_hash,
            n_ordered_products=n_ordered_products,
        )
        order.save()
        # retrieve order ID and set variable
        order_id = order.id
        # augmenting amount of ordered food
        timeslot_db = Inventory.objects.get(time_slot=class_date)
        timeslot_db.received_orders += n_ordered_products
        timeslot_db.save()
        # TODO: check again if timeslot matches ordered food - probably not necessary
        pdf = get_pdf(order)
        timeslot = class_date.strftime("%A %d. %B %H:%M")

        with mail.get_connection() as connection:
            email = sendmail(mailto=form_data["email"],
                             name=form_data["name"],
                             price=price,
                             timeslot=timeslot,
                             order_id=order.id,
                             connection=connection)
            email.attach(
                f"Bestellbestätigung-{order.id}.pdf", pdf, 'application/pdf')
            email.send()
        # return render(self.request, 'orders/success.html', {
        #     'order_id': order_id, "order_hash": order_hash
        # })
        return super().form_valid(form)
    
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['price'] = 12
        return context




def UpdateInventory():
    """function to update the inventory e.g. after modifying or deleting an order"""
    inventory = Inventory.objects.all()
    
    for item in inventory:
        qs = Order.objects.filter(time_slot=item.time_slot)
        
        n_products = 0 
        for order in qs:
            n_products += order.n_ordered_products
        if item.received_orders != n_products:
            print(
                f"Changing n products in timeslot {item.time_slot} from {item.received_orders} to {n_products}")
            item.received_orders = n_products
            item.save()
            
