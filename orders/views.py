from django.contrib.auth import authenticate, login
import os
import secrets
from django.db import connection
from django.shortcuts import render, redirect
from django.views.generic import View

from django.http import HttpResponseRedirect, JsonResponse
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

def calculateprice(form_product_data, n_products=False, get_summary=False):
    price = 0
    products = 0
    summary = []
    for item in form_product_data:
        if form_product_data[item] is None:
            continue
        price += form_product_data[item] * Product.objects.get(short_title=item).price
        products += form_product_data[item]
        if get_summary:
            summary.append(f"{item}({form_product_data[item]}x)")
    if get_summary:
        summary = ', '.join(summary)
    if n_products:
        if get_summary:
            return price, products, summary
        return price, products
    if get_summary:
        return price, summary
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
        # check if order already exists and if so don't save it
        duplicate_order = Order.objects.filter(name=personal_details["name"],
                                           email=personal_details["email"],
                                           time_slot=class_date,
                                           ordered_products=products)
        is_duplicate = duplicate_order.count()

        if n_ordered_products > 50:
            with mail.get_connection() as connection:
                email = EmailMessage(
                    subject=f'[Bestellportal] Limit exceeded',
                    body=f"""Order limit exceeded

                    name: {personal_details["name"]}
                    email: {personal_details["email"]}
                    phone: {personal_details["phone"]}
                    comments: {personal_details["comments"]}
                    time_slot: {class_date}
                    price_total: {price}
                    ordered_products: {products}
                    order_hash: {order_hash}
                    n_ordered_products: {n_ordered_products}
                    """,
                    from_email='"Bestellung BMK Buggingen"<bestellung@bmk-buggingen.de>',
                    to=["bestellung@bmk-buggingen.de"],
                    connection=connection
                )
            email.send()
            return render(self.request, 'orders/failed-limit_exceeded.html')
        if is_duplicate > 0:
            print("This is an Order duplicate. Please get in touch with us!")
            with mail.get_connection() as connection:
                email = EmailMessage(
                    subject=f'[Bestellportal] Duplication Error',
                    body=f"""Eine Bestellung wurde zweifach aufgegeben 
                    
                    products: {duplicate_order[0].ordered_products}
                    
                    ID: {duplicate_order[0].id}
                    time_slot: {duplicate_order[0].time_slot}
                    name: {duplicate_order[0].name}
                    mail: {duplicate_order[0].email}
                    """,
                    from_email='"Bestellung BMK Buggingen"<bestellung@bmk-buggingen.de>',
                    to=["bestellung@bmk-buggingen.de"],
                    connection=connection
                )
            email.send()
            return render(self.request, 'orders/failed.html')
        
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

def ClosedOrdersView(request):
    return render(request, "orders/closed_orders.html")


# @login_required
class order_detail_view(FormView):
    form_class = OrderProductEditForm
    success_url = reverse_lazy('orders/success.html')
    template_name = 'orders/crispy_form.html'



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
            order_type=form_data["order_type"],
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


@login_required
def order_overview_view(request):
    """"""
    orders = Order.objects.all().order_by("id")
    return render(request, "orders/overview.html",
                  {'orders': orders,
                   'updated': timezone.now()
                   })


@login_required
def order_lists_distribution(request, slot):
    sql_query = """
        SELECT time_slot, price_total, order_summary, name, id, comments 
        FROM orders_order 
        WHERE price_total > 0  AND time_slot > '{}' AND time_slot < '{}'
        ORDER BY time_slot ASC
        """
    day_label = ""
    if slot == "sunday-lunch":
        sql_query = sql_query.format(
            '2021-07-18 10:00:00+02:00', '2021-07-18 15:00:00+02:00'
            )
        day_label = "Sonntag Mittag, 18.07.2021"
    elif slot == "sunday-evening":
        sql_query = sql_query.format(
            '2021-07-18 15:00:00+02:00', '2021-07-18 20:00:00+02:00'
            )
        day_label = "Sonntag Abend, 18.07.2021"
    elif slot == "monday-lunch":
        sql_query = sql_query.format(
            '2021-07-19 10:00:00+02:00', '2021-07-19 15:00:00+02:00'
            )
        day_label = "Montag Mittag, 19.07.2021"
    else:
        print("not found")
    orders = Order.objects.raw(sql_query)
    # orders = Order.objects.all().values("time_slot",
    #                                     "id",
    #                                     "price_total",
    #                                     "order_summary",
    #                                     "name",
    #                                     "comments").order_by('time_slot')
    return render(request, "orders/distribution-list-overview.html",
                  {'orders': orders,
                   "day_label": day_label
                   })
    # qs = Order.objects.filter(time_slot=item.time_slot)
    # return render(request, "orders/overview.html",
    #               {'orders': orders})
    # SQL query from google portal:
    # "SELECT * WHERE G = 'Sonntag, 23.05.2021' AND I < timeofday '15:00:00' AND F > 1 ORDER BY I ASC"
    # using SQL in django:
    # Person.objects.raw('SELECT * FROM myapp_person')

import pandas as pd
import numpy as np

@login_required
def order_lists_ettiketten(request, timeslot):
    start_query, end_query, _ = getDayQuery(timeslot)
    qs = Order.objects.filter(
        time_slot__gt=start_query,
        time_slot__lt=end_query,
        ).values(
            "time_slot",
            "id",
            "price_total",
            "order_summary",
            "comments",
            "name",
            "phone",
    ).order_by('time_slot')
    df = pd.DataFrame(qs.values(
        "time_slot",
        "id",
        "price_total",
        "order_summary",
        "name",
        "comments",
        "phone"
    ))
    day_order = [timezone.localtime(item["time_slot"]).strftime(
        '%A, %d.%B.%y') for item in qs.values("time_slot")]
    df['day_order'] = day_order
    time_order = [timezone.localtime(item["time_slot"]).strftime(
        '%H:%M') for item in qs.values("time_slot")]
    df['time_order'] = time_order
    fields = [
        "time_order",
        "day_order",
        "id",
        "price_total",
        "order_summary",
        "name",
        "comments",
        "phone"
        ]
    df = df[fields]
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename=Etiketten_{timeslot}.csv'
    header = ["Abholzeit", "Abholtag", "Bestellnummer", "Preis", "Bestellung",
              "Name", "Kommentar",  "Telefon"]
    df.to_csv(path_or_buf=response, sep=';', float_format='%.2f',
              index=False, decimal=",", header=header)
    return response


def getDayQuery(timeslot):
    if timeslot == "sunday-lunch":
        start_query = '2021-07-18 10:00:00+02:00'
        end_query = '2021-07-18 15:00:00+02:00'
        day_label = "Sonntag Mittag, 18.07.2021"
        return start_query, end_query, day_label
    elif timeslot == "sunday-evening":
        start_query = '2021-07-18 15:00:00+02:00'
        end_query = '2021-07-18 20:00:00+02:00'
        day_label = "Sonntag Abend, 18.07.2021"
        return start_query, end_query, day_label

    elif timeslot == "monday-lunch":
        start_query = '2021-07-19 10:00:00+02:00'
        end_query = '2021-07-19 15:00:00+02:00'
        day_label = "Montag Mittag, 19.07.2021"
        return start_query, end_query, day_label

    elif timeslot == "all":
        start_query = '2021-07-18 10:00:00+02:00'
        end_query = '2021-07-19 15:00:00+02:00'
        day_label = "Gesamt"
        return start_query, end_query, day_label


# @login_required
def order_lists_pivot(request, pivot, timeslot):
   start_query, end_query, day_label = getDayQuery(timeslot)
   qs = Order.objects.filter(
       time_slot__gt=start_query,
       time_slot__lt=end_query,
   ).values(
       "time_slot",
       "id",
       "price_total",
       "order_summary",
       "comments",
       "name",
       "phone",
   ).order_by('time_slot')
   ordered_products = [i["ordered_products"]
                       for i in qs.values("ordered_products")]

   df = pd.DataFrame(qs.values(
       "time_slot",
       "id",
       "price_total",
       "order_summary",
       "name",
       "comments",
       "phone"
   ))
   day_order = [timezone.localtime(item["time_slot"]).strftime(
       '%A, %d.%B.%y') for item in qs.values("time_slot")]
   df['day_order'] = day_order
   time_order = [timezone.localtime(item["time_slot"]).strftime(
       '%H:%M') for item in qs.values("time_slot")]
   df['time_order'] = time_order
   df_def = pd.DataFrame(ordered_products)

   df = pd.concat([df, df_def], axis=1)
   df = df.fillna(0)
   values = ["Salat", "Pommes", "SteakBrot", "SteakPom", "PuteBrot", "PutePommes",
       "WurstWeckle", "WurstPommes", "CamembertWeckle", "CamembertPommes"]
   
   if pivot == 'pivot':
        table = pd.pivot_table(df, values=values, index=[
                            "day_order","time_order"], aggfunc=np.sum,
                            margins=True,
                            fill_value=0)
        table = table.reindex(values, axis=1)
        context = {'pivot': table.to_html,
                    'updated': timezone.now(),
                    'label': day_label
                    }
        return render(request, 'orders/pivot.html', context)

   elif pivot == 'pivot-summary':
        subcategories = {
            "Salat": ["Salat"],
            "Pommes": ["Pommes",
                        "SteakPom",
                        "PutePommes",
                        "WurstPommes",
                        "CamembertPommes",
                        ],
            "Steak": [
                "SteakBrot",
                "SteakPom",
            ],
            "Putensteak": [
                "PuteBrot",
                "PutePommes",
            ],
            "Wurst": [
                "WurstWeckle",
                "WurstPommes"
            ],
            "Camembert": [
                "CamembertWeckle",
                "CamembertPommes",
                "CamembertPommes",
            ],
            "Brot": [
                "SteakBrot",
                "PuteBrot",
            ],
            "Weckle": [
                "CamembertWeckle",
                "WurstWeckle"
            ]}
        for elem in subcategories:
            df[elem] = df[subcategories[elem]].sum(axis=1)
        values = list(subcategories.keys())
        table = pd.pivot_table(df, values=values, index=[
                            "day_order","time_order"], aggfunc=np.sum,
                            margins=True,
                            fill_value=0)
        # print(pd.pivot_table(df, values=values, index=[
        #     "day_order"], aggfunc=np.sum,
        #     margins=True,
        #     fill_value=0).reset_index().query('day_order=="All"'))
        table = table.reindex(values, axis=1)
        context = {'pivot': table.to_html,
                    'updated': timezone.now(),
                    'label': day_label,
                    }
        return render(request, 'orders/pivot.html', context)

def pivotOverviewView(request):
    return render(request, 'orders/pivot-overview.html')
# TODO: statistics: per time slot, orders, amount of food


class CharView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'orders/stat-charts.html')


def get_data(request, *args, **kwargs):
    start_query, end_query, day_label = getDayQuery("all")
    qs = Order.objects.filter(
        time_slot__gt=start_query,
        time_slot__lt=end_query,
        price_total__gt=0,
    ).values(
        "time_slot",
        "price_total",
        "n_ordered_products",
        "time_stamp",
        "order_type",
    ).order_by('time_stamp')
    df = pd.DataFrame(qs.values(
        "time_slot",
        "price_total",
        "n_ordered_products",
        "time_stamp",
        "order_type",
   ))

    day_order = [timezone.localtime(item["time_slot"]).strftime(
        '%y-%m-%d') for item in qs.values("time_slot")]
    df['day_order'] = day_order
    time_order = [timezone.localtime(item["time_slot"]).strftime(
       '%H:%M') for item in qs.values("time_slot")]
    df['time_order'] = time_order
    ordered = [timezone.localtime(item["time_stamp"]).strftime(
        '%y-%m-%d') for item in qs.values("time_stamp")]
    df['ordered'] = ordered
    df['count'] = np.ones(len(df))
    df['count_weighted'] = np.ones(len(df)) * df["n_ordered_products"]
    df = df.fillna(0)
    df_grouped_accu = df.groupby(['ordered']).sum().cumsum().reset_index()
    df_grouped = df.groupby(['ordered']).sum().reset_index()
    
    df_time_slot_grouped = df.groupby(
        ['day_order', 'time_order']).sum().reset_index()
    df_type_grouped = df.groupby(['order_type']).sum().reset_index()
    
    data = {
        "n_orders_accu":{
            "labels": list(df_grouped_accu["ordered"].values),
            "chartLabel": "Bestellungen kumuliert",
            "chartdata": list(df_grouped_accu["count"].values),
        },
        "n_orders_day":{
            "labels": list(df_grouped["ordered"].values),
            "chartLabel": "Bestellungen pro Tag",
            "chartdata": list(df_grouped["count"].values),
        },
        "n_products_accu":{
            "labels": list(df_grouped_accu["ordered"].values),
            "chartLabel": "Essensbestellungen kumuliert",
            "chartdata": list(df_grouped_accu["n_ordered_products"].astype(float).values),
        },
        "n_products_day":{
            "labels": list(df_grouped["ordered"].values),
            "chartLabel": "Essensbestellungen pro Tag",
            "chartdata": list(df_grouped["n_ordered_products"].astype(float).values),
        },
        "timeslot_sunday":{
            "labels": list(df_time_slot_grouped.query('day_order=="21-07-18"')["time_order"].values),
            "chartLabel": "Essen pro Timeslot",
            "chartdata": list(df_time_slot_grouped.query('day_order=="21-07-18"')["n_ordered_products"].astype(float).values),
        },
        "timeslot_monday":{
            "labels": list(df_time_slot_grouped.query('day_order=="21-07-19"')["time_order"].values),
            "chartLabel": "Essen pro Timeslot",
            "chartdata": list(df_time_slot_grouped.query('day_order=="21-07-19"')["n_ordered_products"].astype(float).values),
        },
        "order_type": {
            "labels": list(df_type_grouped["order_type"].values),
            "chartLabel": "Bestellform",
            "chartdata": list(df_type_grouped["count"].values),
        },
        "order_type_weighted": {
            "labels": list(df_type_grouped["order_type"].values),
            "chartLabel": "Bestellform gewichtet",
            "chartdata": list(df_type_grouped["count_weighted"].values),
        },
        "price_accu": {
            "labels": list(df_grouped_accu["ordered"].values),
            "chartLabel": "Bestellungen kumuliert",
            "chartdata": list(df_grouped_accu["price_total"].values),
        },
        "price_day": {
            "labels": list(df_grouped["ordered"].values),
            "chartLabel": "Bestellungen pro Tag",
            "chartdata": list(df_grouped["price_total"].values),
        },
    }
    return JsonResponse(data) # http response


# statistics:
# - #bestellungen pro Tag kumuliert 
# - bestellte Essen pro Tag kumuliert
# - Einnahmen pro Tag kumuliert
# - Essen pro timeslots
#   - sunday-lunch, sunday-evening, monday-lunch
# order_type pie chart
# table with per day orders and limit
# detailed table

def TableOverviewView(request):
    template = "orders/table_overview.html"
    df, category_values, subcategory_values = GetSummaryStats("all")
    df_sun_lunch, _, _ = GetSummaryStats("sunday-lunch")
    df_sun_evening, _, _ = GetSummaryStats("sunday-evening")
    df_mon_lunch, _, _ = GetSummaryStats("monday-lunch")
    
    df_category = df[category_values].sum(axis=0).reset_index()
    df_category.columns = ["product", "count"]
    df_sun_lunch_category = df_sun_lunch[category_values].sum(axis=0).reset_index()
    df_sun_lunch_category.columns = ["product", "count"]
    df_category["sun_lunch"] = df_sun_lunch_category["count"]
    df_sun_evening_category = df_sun_evening[category_values].sum(axis=0).reset_index()
    df_sun_evening_category.columns = ["product", "count"]
    df_category["sun_evening"] = df_sun_evening_category["count"]
    df_mon_lunch_category = df_mon_lunch[category_values].sum(axis=0).reset_index()
    df_mon_lunch_category.columns = ["product", "count"]
    df_category["mon_lunch"] = df_mon_lunch_category["count"]
    category_all = df_category.to_dict('records')
    total = {'product': 'Gesamt',
                         'count': df_category["count"].sum(),
                        'sun_lunch': df_category["sun_lunch"].sum(),
                        'sun_evening': df_category["sun_evening"].sum(),
                        'mon_lunch': df_category["mon_lunch"].sum()}
   
    df = df[subcategory_values].sum(axis=0).reset_index()
    df.columns = ["product", "count"]
    df_sun_lunch = df_sun_lunch[subcategory_values].sum(axis=0).reset_index()
    df_sun_lunch.columns = ["product", "count"]
    df["sun_lunch"] = df_sun_lunch["count"]
    df_sun_evening = df_sun_evening[subcategory_values].sum(axis=0).reset_index()
    df_sun_evening.columns = ["product", "count"]
    df["sun_evening"] = df_sun_evening["count"]
    df_mon_lunch = df_mon_lunch[subcategory_values].sum(axis=0).reset_index()
    df_mon_lunch.columns = ["product", "count"]
    df["mon_lunch"] = df_mon_lunch["count"]
    subcategory_all = df.to_dict('records')
    context = {
        "category_all": category_all,
        "subcategory_all": subcategory_all,
        "total": total,
        'updated': timezone.now()
        }

    return render(request, template, context)
    
    
def GetSummaryStats(timeslot):
    start_query, end_query, day_label = getDayQuery(timeslot)
    qs = Order.objects.filter(
        time_slot__gt=start_query,
        time_slot__lt=end_query,
    ).values(
        "time_slot",
        "id",
        "price_total",
        "order_summary",
        "comments",
        "name",
        "phone",
    ).order_by('time_slot')
    ordered_products = [i["ordered_products"]
                        for i in qs.values("ordered_products")]

    df = pd.DataFrame(qs.values(
        "time_slot",
        "id",
        "price_total",
        "order_summary",
        "name",
        "comments",
        "phone"
    ))
    day_order = [timezone.localtime(item["time_slot"]).strftime(
        '%A, %d.%B.%y') for item in qs.values("time_slot")]
    df['day_order'] = day_order
    time_order = [timezone.localtime(item["time_slot"]).strftime(
        '%H:%M') for item in qs.values("time_slot")]
    df['time_order'] = time_order
    df_def = pd.DataFrame(ordered_products)

    df = pd.concat([df, df_def], axis=1)
    df = df.fillna(0)
    category_values = ["Salat", "Pommes", "SteakBrot", "SteakPom", "PuteBrot", "PutePommes",
        "WurstWeckle", "WurstPommes", "CamembertWeckle", "CamembertPommes"]
    
    subcategories = {
        "Salat": ["Salat"],
        "Pommes-gesamt": ["Pommes",
                    "SteakPom",
                    "PutePommes",
                    "WurstPommes",
                    "CamembertPommes",
                    ],
        "Steak": [
            "SteakBrot",
            "SteakPom",
        ],
        "Putensteak": [
                "PuteBrot",
                "PutePommes",
            ],
        "Wurst": [
                "WurstWeckle",
                "WurstPommes"
            ],
        "Camembert": [
                "CamembertWeckle",
                "CamembertPommes",
                "CamembertPommes",
            ],
        "Brot": [
                "SteakBrot",
                "PuteBrot",
            ],
        "Weckle": [
                "WurstWeckle",
                "CamembertWeckle"
            ]}
    for elem in subcategories:
        df[elem] = df[subcategories[elem]].sum(axis=1)
    subcategory_values = list(subcategories.keys())
    
    df = df[category_values + subcategory_values]
    # removing duplicated columns -> in this case "Salat"
    df = df.loc[:, ~df.columns.duplicated()]
    return df, category_values, subcategory_values
