from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Создать группы и назначить права. Повторный запуск безопасен.'

    def handle(self, *args, **options):
        rules = {
            'Клиент': {'machine': ['view'], 'maintenance': ['view', 'add', 'change'], 'claim': ['view'], 'directory': ['view']},
            'Сервисная организация': {'machine': ['view'], 'maintenance': ['view', 'add', 'change'],
                                      'claim': ['view', 'add', 'change'], 'directory': ['view']},
            'Менеджер': {model: ['view', 'add', 'change'] for model in ['machine', 'maintenance', 'claim', 'directory']},
        }
        for name, models in rules.items():
            group, _ = Group.objects.get_or_create(name=name)
            codes = [f'{action}_{model}' for model, actions in models.items() for action in actions]
            group.permissions.set(Permission.objects.filter(content_type__app_label='service', codename__in=codes))
        self.stdout.write(self.style.SUCCESS('Группы созданы.'))
