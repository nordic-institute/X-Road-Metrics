import datetime
import json

from django import forms

# Django 2.2 does not support this format by default
INPUT_FORMATS = [
    '%Y-%m-%dT%H:%M:%S',
]


class HarvestForm(forms.Form):
    from_dt = forms.DateTimeField(required=True, input_formats=INPUT_FORMATS)
    until_dt = forms.DateTimeField(required=False, input_formats=INPUT_FORMATS)
    offset = forms.IntegerField(required=False)
    limit = forms.IntegerField(required=False, min_value=0)
    # compatibility with Django 2.2
    order = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        from_dt = cleaned_data.get('from_dt')
        until_dt = cleaned_data.get('until_dt')
        if from_dt and until_dt:
            if from_dt > until_dt:
                self.add_error('from_dt', 'Ensure the value is not later than until_dt')
                self.add_error('until_dt', 'Ensure the value is not earlier than from_dt')
        return cleaned_data

    def clean_from_dt(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        from_dt_value = self.cleaned_data['from_dt']
        if now < from_dt_value:
            raise forms.ValidationError(
                'Ensure the value is not later than the current date and time'
            )
        return from_dt_value

    def clean_order(self):
        ALLOWED_ORDER_KEYS = ['column', 'order']
        ALLOWED_ORDER_ORDER_VALUES = ['ASC', 'DESC']

        order = self.cleaned_data.get('order')
        if order:
            try:
                order = json.loads(order)
            except json.decoder.JSONDecodeError:
                raise forms.ValidationError('Ensure "order" is valid json')
            for key, value in order.items():
                if key not in ALLOWED_ORDER_KEYS:
                    raise forms.ValidationError('Ensure only "column" and "order" are set as keys')
            if order['order'].upper() not in ALLOWED_ORDER_ORDER_VALUES:
                raise forms.ValidationError('Ensure only "ASC" or "DESC" is set for order')
        return order
