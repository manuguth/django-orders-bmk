import os
import secrets
from django.db import connection
from django.shortcuts import render

from django.http import HttpResponseRedirect
from formtools.wizard.views import SessionWizardView
from django.core.mail import EmailMessage
from django.core import mail
from django.core.files import File
from io import BytesIO

from django.views.generic import FormView, TemplateView
from django.urls import reverse_lazy

from .forms import(
    OrderModelForm,
    OrderProductForm,
    OrderTimeSlotForm,
    OrderCheckoutForm,
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


def render_pdf_view(request):
# def render_pdf_view():
    # template_path = 'orders/invoice_template.html'
    template_path = 'orders/invoice-new.html'
    context = {'myvar': 'this is your template context'}
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)
    

    # create a pdf
    pisa_status = pisa.CreatePDF(
        html, dest=response, link_callback=link_callback)
    # if error then show some funy view
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    # purch_upd = purchase.objects.get(pk=purch_id)
    # purch_upd.receipt = File(receipt_file, filename)
    return response


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
    

def sendmail(mailto, name, price, timeslot, order_id, connection):
    message = f"""
Guten Tag {name}, 

vielen Dank für Ihre Bestellung. Anbei erhalten Sie Ihre Bestellbestätigung als pdf-Datei.

Bitte bezahlen Sie den fälligen Betrag von {price} € bei Abholung Ihrer Bestellung am {timeslot} passend in bar.

Bei Rückfragen stehen wir Ihnen gerne zur Verfügung unter bestellung@bmk-buggingen.de.

Ihre Bergmannskapelle Buggingen e.V.
"""
    email = EmailMessage(
        subject=f'Bestellbestätigung Maihock To Go - Bestellung {order_id}',
        body=message,
        from_email='"Bestellung BMK Buggingen"<bestellung@bmk-buggingen.de>',
        to=[mailto],
        bcc=['bestellung@bmk-buggingen.de'],
        connection=connection
        # reply_to=['another@example.com'],
        # headers={'Message-ID': 'foo'},
    )
    return email

def generatepdf(data):
    # possibility html -> pdf https://xhtml2pdf.readthedocs.io/en/latest/usage.html
    # maybe? https://github.com/matthiask/pdfdocument
    # looks the right thing to use for invoice: https://www.reportbro.com/home/index
    print("start generating PDF")


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
        print(form_list[0].cleaned_data)
        print([form.cleaned_data for form in form_list])
        personal_details = super().get_cleaned_data_for_step("personaldetails")
        products = super().get_cleaned_data_for_step("productchoice")
        price, n_ordered_products = calculateprice(products, n_products=True)
        class_date = timezone.localtime(
            parse_datetime(super().get_cleaned_data_for_step("timeslot")["time_slot"]))
        timeslot = class_date.strftime("%A %d. %B %H:%M")
        
        # TODO: write to database
        # create a unique hash for each order
        order_hash = secrets.token_urlsafe(16)
        response = render_pdf_view()
        receipt_file = BytesIO(response.content)

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
            invoice=receipt_file,
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

        
        with mail.get_connection() as connection:
            email = sendmail(mailto=personal_details["email"],
                             name=personal_details["name"],
                            price=price,
                            timeslot=timeslot,
                             order_id=order_id,
                            connection=connection)
            email.send()
        return render(self.request, 'orders/success.html', {
            'form_data': [form.cleaned_data for form in form_list],
            'order_id': order_id
        })
    

class SuccessView(TemplateView):
    template_name = 'orders/success.html'


