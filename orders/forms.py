import os
import itertools
import subprocess
from .models import Order
from django import forms
from inventory.models import Inventory
from products.models import Product
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit
from crispy_forms.layout import Layout, Div, Submit, Row, Column, Field
from django.utils.safestring import mark_safe
from django.utils import timezone
import locale

if 'WEBSITE_HOSTNAME' not in os.environ:
    locale.setlocale(locale.LC_ALL, 'de_DE')
elif 'WEBSITE_HOSTNAME' in os.environ:
    locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')

    

def boldlabel(label):
    return mark_safe(f"<strong>{label}</strong>")

class OrderModelForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
          
    name = forms.CharField(max_length=220,
                            label=boldlabel('Name'),
                            widget=forms.TextInput(attrs={'placeholder': 'Bitte tragen Sie ihren Namen hier ein.'}))
    email=forms.EmailField(max_length = 220,
        label=boldlabel('E-Mail Adresse'),
        help_text="Sie bekommen nach dem Absenden Ihrer Bestellung eine Bestellbestätigung per E-Mail zugeschickt.",
        widget=forms.TextInput(attrs={'placeholder': 'Bitte tragen Sie ihre E-Mail Adresse hier ein.'}))
    phone = forms.CharField(max_length=220,
        label=boldlabel('Telefonnummer'),
        widget=forms.TextInput(attrs={'placeholder': 'Bitte tragen Sie ihre Telefonnummer hier ein.'}),
        help_text='Damit wir Sie bei Rückfragen telefonisch erreichen können, hinterlegen Sie bitte Ihre Telefonnummer.')
    comments = forms.CharField(max_length=220,
        label=boldlabel('Kommentar'),
                               widget=forms.TextInput(attrs={'placeholder': 'Möchten Sie uns noch etwas zu Ihrer Bestellung mitteilen?'}), required=False)
    check_me_out = forms.BooleanField(required=True, label=boldlabel("Zustimmung zur Verwendung der Kontaktdaten für den Zweck der Bestellung."), help_text="Wir verwenden Ihre Kontaktdaten nur für den Zweck Ihrer Bestellung und geben Sie nicht an Dritte weiter.")
    

class OrderProductForm(forms.Form):  
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Product.objects.all()
        fields = [[i.short_title, i.display_order, i.id] for i in qs]
        fields = sorted(fields, key=lambda l: l[1])
        field_names = [i[0] for i in fields]
        field_ids = [i[2] for i in fields]
        
        for i in range(len(qs)):
            entry = Product.objects.get(id=field_ids[i])
            field_name = entry.short_title
            self.fields[field_name] = forms.IntegerField(max_value=40, 
                min_value=0,
                required=False,
                label=boldlabel(f"{entry.title} - {entry.price} €"),
                help_text=entry.description,
                widget=forms.NumberInput(
                    attrs={'placeholder': f"Geben Sie Ihre gewünschte Anzahl an '{entry.title}' an."})
                )


class OrderTimeSlotForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Inventory.objects.all()
        slots = self.GetTimeSlots(qs)
        
        STATES = (
            ('', 'Wählen Sie Ihre Abholzeit...'),
            *slots
        )

        self.fields["time_slot"] = forms.ChoiceField(choices=STATES, label=boldlabel("Abholzeit"),
                                                     help_text="Bitte wählen Sie eine der oben angegebenen Abholzeiten aus. (Damit wir Ihre Bestellung bestmöglich vorbereiten können, können wir nur eine limitierte Anzahl an Bestellungen pro Abholzeit annehmen.) ")

    def GetTimeSlots(self, qs):
        # TODO: check also if the order doesn't exceed the order limit per time slot!!
        slots = []
        for entry in qs:
            if entry.received_orders < entry.order_limit:
                class_date = timezone.localtime(entry.time_slot)
                slots.append(
                    (entry.time_slot, class_date.strftime("%A %d. %B %H:%M")))
        return sorted(slots)
    

class OrderCheckoutForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Zum Abschluss benötigen wir noch Ihre Kontaktdaten',
                "check_me_out",
            ),
            ButtonHolder(
                Submit('submit', 'Weiter', css_class='button white')
            )
        )

    check_me_out = forms.BooleanField(required=True, label=boldlabel("Hiermit bestätige ich meine oben aufgeführte Bestellung."),
                                      help_text="")


class OrderProductEditForm(forms.Form):
    def __init__(self, id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        order = Order.objects.get(id=id)
        qs = Product.objects.all()
        fields = [[i.short_title, i.display_order, i.id] for i in qs]
        fields = sorted(fields, key=lambda l: l[1])
        field_names = [i[0] for i in fields]
        field_ids = [i[2] for i in fields]
        def mygrouper(n, iterable):
            args = [iter(iterable)] * n
            return ([Column(f'{e}', css_class='form-group col-md-3 mb-0') for e in t if e != None] for t in itertools.zip_longest(*args))
        grouped_fields = list(mygrouper(4, field_names))
        form_rows = []
        for entry in grouped_fields:
            form_rows.append(Row(*entry,
                css_class='form-row'
            ))
        print(*form_rows)

        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-4 mb-0'),
                Column('email', css_class='form-group col-md-4 mb-0'),
                Column('phone', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            "comments",
            "time_slot",
            *form_rows,
            ButtonHolder(
                Submit('submit', 'Änderung speichern',
                       css_class='button white')
            )
        )
        for i in range(len(qs)):
            entry = Product.objects.get(id=field_ids[i])
            field_name = entry.short_title
            n_ordered = order.ordered_products[field_name]
            self.fields[field_name] = forms.IntegerField(min_value=0,
                                                         required=False,
                                                         label=entry.short_title,
                                                         initial=0 if n_ordered is None else n_ordered
                                                         )

        self.fields["name"] = forms.CharField(max_length=220,
                            label=boldlabel('Name'), initial=order.name)
        self.fields["email"] = forms.EmailField(max_length=220,
                                label=boldlabel('E-Mail Adresse'),
                                initial=order.email)
        self.fields["phone"] = forms.CharField(max_length=220,
                                label=boldlabel('Telefonnummer'),
                                initial=order.phone)
        self.fields["comments"] = forms.CharField(max_length=220,
                                label=boldlabel('Kommentar'),
                                initial=order.comments, required=False)
        
        qs_inventory = Inventory.objects.all()
        slots = self.GetTimeSlots(qs_inventory)

        STATES = tuple(slots)

        self.fields["time_slot"] = forms.ChoiceField(choices=STATES, label=boldlabel("Abholzeit"),
                                                     initial=order.time_slot)

    def GetTimeSlots(self, qs):
        slots = []
        for entry in qs:
            if entry.received_orders < entry.order_limit:
                class_date = timezone.localtime(entry.time_slot)
                slots.append(
                    (entry.time_slot, class_date.strftime("%A %d. %B %H:%M")))
            else:
                class_date = timezone.localtime(entry.time_slot)
                slots.append(
                    (entry.time_slot, f'{class_date.strftime("%A %d. %B %H:%M")} - ausgebucht ({entry.received_orders}/{entry.order_limit})'))
        return sorted(slots)


class OrderProductInternalForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        qs = Product.objects.all()
        fields = [[i.short_title, i.display_order, i.id] for i in qs]
        fields = sorted(fields, key=lambda l: l[1])
        field_names = [i[0] for i in fields]
        field_ids = [i[2] for i in fields]
        def mygrouper(n, iterable):
            args = [iter(iterable)] * n
            return ([Column(f'{e}', css_class='form-group col-md-3 mb-0') for e in t if e != None] for t in itertools.zip_longest(*args))
        grouped_fields = list(mygrouper(4, field_names))
        form_rows = []
        for entry in grouped_fields:
            form_rows.append(Row(*entry,
                css_class='form-row'
            ))
        print(*form_rows)

        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-4 mb-0'),
                Column('email', css_class='form-group col-md-4 mb-0'),
                Column('phone', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            "comments",
            "time_slot",
            *form_rows,
            ButtonHolder(
                Submit('submit', 'Bestellung speichern',
                       css_class='button white')
            )
        )
        for i in range(len(qs)):
            entry = Product.objects.get(id=field_ids[i])
            field_name = entry.short_title
            self.fields[field_name] = forms.IntegerField(min_value=0,
                                                         required=False,
                                                         label=entry.short_title,
                                                         )

        self.fields["name"] = forms.CharField(max_length=220,
                            label=boldlabel('Name'))
        self.fields["email"] = forms.EmailField(max_length=220,
                                label=boldlabel('E-Mail Adresse'), 
                                initial="bestellung@bmk-buggingen.de")
        self.fields["phone"] = forms.CharField(max_length=220,
                                label=boldlabel('Telefonnummer'))
        self.fields["comments"] = forms.CharField(max_length=220,
                                label=boldlabel('Kommentar'))
        
        qs_inventory = Inventory.objects.all()
        slots = self.GetTimeSlots(qs_inventory)

        STATES = tuple(slots)

        self.fields["time_slot"] = forms.ChoiceField(choices=STATES, label=boldlabel("Abholzeit"))

    def GetTimeSlots(self, qs):
        slots = []
        for entry in qs:
            if entry.received_orders < entry.order_limit:
                class_date = timezone.localtime(entry.time_slot)
                slots.append(
                    (entry.time_slot, class_date.strftime("%A %d. %B %H:%M")))
            else:
                class_date = timezone.localtime(entry.time_slot)
                slots.append(
                    (entry.time_slot, f'{class_date.strftime("%A %d. %B %H:%M")} - ausgebucht ({entry.received_orders}/{entry.order_limit})'))
        return sorted(slots)
