from django import forms
from django.contrib.auth.models import User
from .models import Machine, Maintenance, Claim, Directory
from .permissions import available_machines


class UserChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.get_full_name() or obj.username


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field, forms.DateField):
                field.widget = forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs['rows'] = 3


class MachineForm(StyledModelForm):
    client = UserChoiceField(label='Клиент', queryset=User.objects.filter(groups__name='Клиент'))
    service_company = UserChoiceField(label='Сервисная компания', queryset=User.objects.filter(groups__name='Сервисная организация'))

    class Meta:
        model = Machine
        fields = '__all__'


class MachineRecordForm(StyledModelForm):
    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['machine'].queryset = available_machines(user)

    def clean(self):
        data = super().clean()
        if data.get('machine'):
            self.instance.service_company = data['machine'].service_company
        return data


class MaintenanceForm(MachineRecordForm):
    class Meta:
        model = Maintenance
        exclude = ['service_company']


class ClaimForm(MachineRecordForm):
    class Meta:
        model = Claim
        exclude = ['service_company']


class DirectoryForm(StyledModelForm):
    class Meta:
        model = Directory
        fields = '__all__'
