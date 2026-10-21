from .models import Machine

MANAGER = 'Менеджер'
CLIENT = 'Клиент'
SERVICE = 'Сервисная организация'


def role(user):
    if not user.is_authenticated:
        return 'Гость'
    if user.is_superuser:
        return MANAGER
    for name in (MANAGER, SERVICE, CLIENT):
        if user.groups.filter(name=name).exists():
            return name
    return 'Без роли'


def available_machines(user):
    user_role = role(user)
    if user_role == MANAGER:
        return Machine.objects.all()
    if user_role == CLIENT:
        return Machine.objects.filter(client=user)
    if user_role == SERVICE:
        return Machine.objects.filter(service_company=user)
    return Machine.objects.none()


def can_edit(user, section):
    user_role = role(user)
    return (user_role == MANAGER or
            section == 'maintenances' and user_role in (CLIENT, SERVICE) or
            section == 'claims' and user_role == SERVICE)
