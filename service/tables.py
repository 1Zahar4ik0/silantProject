from django import forms
from django.contrib.auth.models import User
from .models import Machine, Maintenance, Claim
from .forms import MachineForm, MaintenanceForm, ClaimForm, UserChoiceField
from .permissions import available_machines

SECTIONS = {
    'machines': {'model': Machine, 'form': MachineForm, 'title': 'Технические данные', 'date': 'shipment_date',
                 'filters': ['machine_model', 'engine_model', 'transmission_model', 'steer_axle_model', 'drive_axle_model']},
    'maintenances': {'model': Maintenance, 'form': MaintenanceForm, 'title': 'Техническое обслуживание',
                    'date': 'maintenance_date', 'filters': ['maintenance_type', 'machine', 'service_company']},
    'claims': {'model': Claim, 'form': ClaimForm, 'title': 'Рекламации', 'date': 'failure_date',
               'filters': ['failure_node', 'recovery_method', 'service_company']},
}
PUBLIC_FIELDS = [f.name for f in Machine._meta.fields if f.name != 'id'][:10]


def scoped_records(user, section):
    machines = available_machines(user)
    model = SECTIONS[section]['model']
    qs = machines if section == 'machines' else model.objects.filter(machine__in=machines)
    return qs.select_related()


def filter_records(qs, section, params):
    config = SECTIONS[section]
    form = forms.Form(params)
    for name in config['filters']:
        field = config['model']._meta.get_field(name)
        options = field.related_model.objects.filter(pk__in=qs.values(name)).distinct()
        cls = UserChoiceField if field.related_model == User else forms.ModelChoiceField
        form.fields[name] = cls(queryset=options, required=False, label=field.verbose_name, empty_label='Все')
    form.fields['order'] = forms.ChoiceField(label='Порядок по дате', required=False,
                                            choices=[('', 'Сначала новые'), ('asc', 'Сначала старые')])
    if form.is_valid():
        for name in config['filters']:
            if form.cleaned_data[name]:
                qs = qs.filter(**{name: form.cleaned_data[name]})
        prefix = '' if form.cleaned_data['order'] == 'asc' else '-'
        qs = qs.order_by(prefix + config['date'], 'pk')
    else:
        qs = qs.none()
    return qs, form


def field_value(obj, name):
    value = getattr(obj, name)
    if isinstance(value, User):
        return value.get_full_name() or value.username
    return value


def columns_for(model, public=False):
    fields = [f for f in model._meta.fields if f.name != 'id' and (not public or f.name in PUBLIC_FIELDS)]
    columns = [(f.name, f.verbose_name) for f in fields]
    if model == Claim:
        columns.insert(7, ('downtime', 'Время простоя, дней'))
    return columns
