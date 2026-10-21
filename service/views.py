from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .models import Machine, Directory
from .forms import DirectoryForm
from .permissions import can_edit, role, MANAGER
from .tables import SECTIONS, columns_for, field_value, filter_records, scoped_records


def home(request):
    if request.user.is_authenticated:
        return redirect('records', section='machines')
    number = request.GET.get('serial_number', '').strip()
    machine = Machine.objects.select_related().filter(serial_number=number).first() if number else None
    columns = columns_for(Machine, public=True)
    rows = [] if machine is None else [{'object': machine, 'values': [field_value(machine, n) for n, _ in columns],
                                        'url': reverse('public_machine', args=[machine.serial_number])}]
    return render(request, 'service/home.html', {'number': number, 'searched': 'serial_number' in request.GET,
                                                'columns': columns, 'rows': rows})


def public_machine(request, number):
    obj = get_object_or_404(Machine.objects.select_related(), serial_number=number)
    return render(request, 'service/detail.html', {'object': obj, 'title': f'Машина № {obj.serial_number}',
        'details': [(label, field_value(obj, name)) for name, label in columns_for(Machine, public=True)],
        'back_url': reverse('home')})


def config_for(section):
    if section not in SECTIONS:
        raise Http404
    return SECTIONS[section]


@login_required
def records(request, section):
    config = config_for(section)
    qs, form = filter_records(scoped_records(request.user, section), section, request.GET)
    page = Paginator(qs, 20).get_page(request.GET.get('page'))
    columns = columns_for(config['model'])
    rows = [{'object': obj, 'values': [field_value(obj, n) for n, _ in columns],
             'url': reverse('detail', args=[section, obj.pk])} for obj in page]
    params = request.GET.copy()
    params.pop('page', None)
    return render(request, 'service/list.html', {'section': section, 'title': config['title'], 'filter_form': form,
        'columns': columns, 'rows': rows, 'page_obj': page, 'query': params.urlencode(),
        'editable': can_edit(request.user, section)})


@login_required
def detail(request, section, pk):
    config = config_for(section)
    obj = get_object_or_404(scoped_records(request.user, section), pk=pk)
    return render(request, 'service/detail.html', {'object': obj, 'title': str(obj), 'section': section,
        'details': [(label, field_value(obj, name)) for name, label in columns_for(config['model'])],
        'editable': can_edit(request.user, section), 'back_url': reverse('records', args=[section])})


@login_required
def edit_record(request, section, pk=None):
    config = config_for(section)
    if not can_edit(request.user, section):
        raise PermissionDenied
    obj = get_object_or_404(scoped_records(request.user, section), pk=pk) if pk else None
    kwargs = {'instance': obj}
    if section != 'machines':
        kwargs['user'] = request.user
    form = config['form'](request.POST or None, **kwargs)
    if request.method == 'POST' and form.is_valid():
        obj = form.save()
        messages.success(request, 'Данные сохранены.')
        return redirect('detail', section=section, pk=obj.pk)
    return render(request, 'service/form.html', {'form': form, 'title': ('Изменить' if pk else 'Добавить') + ': ' + config['title'],
        'section': section, 'back_url': reverse('detail', args=[section, pk]) if pk else reverse('records', args=[section])})


@login_required
def directories(request):
    if role(request.user) != MANAGER:
        raise PermissionDenied
    return render(request, 'service/directories.html', {'items': Directory.objects.all(), 'title': 'Справочники',
                                                       'section': 'directories'})


@login_required
def edit_directory(request, pk=None):
    if role(request.user) != MANAGER:
        raise PermissionDenied
    obj = get_object_or_404(Directory, pk=pk) if pk else None
    form = DirectoryForm(request.POST or None, instance=obj)
    if obj:
        form.fields['kind'].disabled = True
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Справочник сохранён.')
        return redirect('directories')
    return render(request, 'service/form.html', {'form': form, 'title': 'Запись справочника',
                                               'section': 'directories', 'back_url': reverse('directories')})
