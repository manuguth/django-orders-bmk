import os
import subprocess
from .models import Order
from django import forms
from inventory.models import Inventory
from products.models import Product
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit
from django.utils.safestring import mark_safe
from django.utils import timezone
import locale

if 'WEBSITE_HOSTNAME' not in os.environ:
    locale.setlocale(locale.LC_ALL, 'de_DE')
# elif 'WEBSITE_HOSTNAME' in os.environ:
#     bashCommand = "echo 'de_DE ISO-8859-1' >> /etc/locale.gen && locale-gen"
#     process = subprocess.call(bashCommand.split(), stdout=subprocess.PIPE)
#     locale.setlocale(locale.LC_ALL, 'de_DE')
    

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
                label=boldlabel(entry.title),
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
        # TODO: Order the choices
        slots = []
        for entry in qs:
            if entry.received_orders < entry.order_limit:
                class_date = timezone.localtime(entry.time_slot)
                slots.append(
                    (entry.time_slot, class_date.strftime("%A %d. %B %H:%M")))
        return slots
    

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
