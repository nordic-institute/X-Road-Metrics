import datetime
import json

from django import forms

DT_FORMAT = '%Y-%m-%dT%H:%M:%S%z'


class HarvestForm(forms.Form):
    from_dt = forms.CharField(required=True)
    until_dt = forms.CharField(required=False)
    offset = forms.IntegerField(required=False)
    limit = forms.IntegerField(required=False, min_value=0)
    from_row_id = forms.IntegerField(required=False)
    # compatibility with Django 2.2
    order = forms.CharField(required=False)

    @staticmethod
    def get_timestamp_with_tz_offset(timestamp):
        timestamp = timestamp.replace(' ', '+')
        return timestamp

    def clean(self):
        from_dt = None
        until_dt = None
        cleaned_data = super().clean()
        from_dt_str = cleaned_data.get('from_dt')
        if from_dt_str:
            from_dt = datetime.datetime.strptime(from_dt_str, DT_FORMAT)
        until_dt_str = cleaned_data.get('until_dt')
        if from_dt_str and until_dt_str:
            until_dt = datetime.datetime.strptime(until_dt_str, DT_FORMAT)
            if from_dt > until_dt:
                self.add_error(
                    'from_dt', 'Ensure the value is not later than until_dt'
                )
                self.add_error(
                    'until_dt', 'Ensure the value is not earlier than from_dt'
                )
        cleaned_data['from_dt'] = from_dt
        cleaned_data['until_dt'] = until_dt
        return cleaned_data

    def clean_from_dt(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        from_dt_value = self.cleaned_data['from_dt']
        from_dt_value = HarvestForm.get_timestamp_with_tz_offset(from_dt_value)
        try:
            from_dt = datetime.datetime.strptime(from_dt_value, DT_FORMAT)
        except ValueError:
            self.add_error('from_dt', f'Ensure the value matches format {DT_FORMAT}')
            return
        if now < from_dt:
            raise forms.ValidationError(
                'Ensure the value is not later than the current date and time'
            )
        return from_dt_value

    def clean_until_dt(self):
        until_dt_value = self.cleaned_data['until_dt']
        if until_dt_value:
            until_dt_value = HarvestForm.get_timestamp_with_tz_offset(until_dt_value)
            try:
                datetime.datetime.strptime(until_dt_value, DT_FORMAT)
            except ValueError:
                self.add_error('until_dt', f'Ensure the value matches format {DT_FORMAT}')
                return
        return until_dt_value

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
