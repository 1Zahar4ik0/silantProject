import secrets
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from service.models import Machine


class Command(BaseCommand):
    help = 'Создать локальные учётные записи для проверки. Пароли сохраняются в .local-credentials.txt.'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('Команда доступна только в режиме разработки.')
        call_command('setup_roles')
        users = []
        admin, created = User.objects.get_or_create(username='admin', defaults={'is_staff': True, 'is_superuser': True})
        if created:
            users.append(admin)
        manager, created = User.objects.get_or_create(username='manager', defaults={'first_name': 'Менеджер Силант'})
        if created:
            manager.groups.add(Group.objects.get(name='Менеджер'))
            users.append(manager)
        machine = Machine.objects.filter(serial_number='0017').first()
        if machine:
            for user in [machine.client, machine.service_company]:
                if not user.has_usable_password():
                    users.append(user)
        lines = []
        for user in users:
            password = secrets.token_urlsafe(12)
            user.set_password(password)
            user.save()
            lines.append(f'{user.username}\t{password}\t{user.get_full_name()}')
        if lines:
            with (settings.BASE_DIR / '.local-credentials.txt').open('a', encoding='utf-8') as output:
                output.write('\n'.join(lines) + '\n')
        self.stdout.write('Учётные данные новых пользователей: .local-credentials.txt. Существующие пароли не изменены.')
