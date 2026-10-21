from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Directory(models.Model):
    class Kind(models.TextChoices):
        MACHINE = 'machine', 'Модель техники'
        ENGINE = 'engine', 'Модель двигателя'
        TRANSMISSION = 'transmission', 'Модель трансмиссии'
        DRIVE_AXLE = 'drive_axle', 'Модель ведущего моста'
        STEER_AXLE = 'steer_axle', 'Модель управляемого моста'
        MAINTENANCE = 'maintenance', 'Вид ТО'
        ORGANIZATION = 'organization', 'Организация, проводившая ТО'
        FAILURE = 'failure', 'Узел отказа'
        RECOVERY = 'recovery', 'Способ восстановления'

    kind = models.CharField('Название справочника', max_length=20, choices=Kind.choices)
    name = models.CharField('Название', max_length=200)
    description = models.TextField('Описание')

    class Meta:
        verbose_name = 'Справочник'
        verbose_name_plural = 'Справочники'
        ordering = ['kind', 'name']
        constraints = [models.UniqueConstraint(fields=['kind', 'name'], name='unique_directory_item')]

    def __str__(self):
        return self.name


def reference(label, kind):
    return models.ForeignKey(Directory, verbose_name=label, on_delete=models.PROTECT,
                             related_name='+', limit_choices_to={'kind': kind})


class Machine(models.Model):
    serial_number = models.CharField('Зав. № машины', max_length=100, unique=True)
    machine_model = reference('Модель техники', 'machine')
    engine_model = reference('Модель двигателя', 'engine')
    engine_number = models.CharField('Зав. № двигателя', max_length=100)
    transmission_model = reference('Модель трансмиссии', 'transmission')
    transmission_number = models.CharField('Зав. № трансмиссии', max_length=100)
    drive_axle_model = reference('Модель ведущего моста', 'drive_axle')
    drive_axle_number = models.CharField('Зав. № ведущего моста', max_length=100)
    steer_axle_model = reference('Модель управляемого моста', 'steer_axle')
    steer_axle_number = models.CharField('Зав. № управляемого моста', max_length=100)
    supply_contract = models.CharField('Договор поставки №, дата', max_length=250)
    shipment_date = models.DateField('Дата отгрузки с завода')
    consignee = models.CharField('Грузополучатель (конечный потребитель)', max_length=250)
    delivery_address = models.TextField('Адрес поставки (эксплуатации)')
    equipment = models.TextField('Комплектация (доп. опции)', blank=True)
    client = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Клиент', on_delete=models.PROTECT,
                               related_name='client_machines', limit_choices_to={'groups__name': 'Клиент'})
    service_company = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Сервисная компания',
                                        on_delete=models.PROTECT, related_name='serviced_machines',
                                        limit_choices_to={'groups__name': 'Сервисная организация'})

    class Meta:
        verbose_name = 'Машина'
        verbose_name_plural = 'Машины'
        ordering = ['-shipment_date', 'serial_number']

    def __str__(self):
        return self.serial_number


class Maintenance(models.Model):
    maintenance_type = reference('Вид ТО', 'maintenance')
    maintenance_date = models.DateField('Дата проведения ТО')
    operating_hours = models.PositiveIntegerField('Наработка, м/час')
    work_order_number = models.CharField('№ заказ-наряда', max_length=100)
    work_order_date = models.DateField('Дата заказ-наряда')
    organization = reference('Организация, проводившая ТО', 'organization')
    machine = models.ForeignKey(Machine, verbose_name='Машина', on_delete=models.PROTECT, related_name='maintenances')
    service_company = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Сервисная компания',
                                        on_delete=models.PROTECT, limit_choices_to={'groups__name': 'Сервисная организация'})

    class Meta:
        verbose_name = 'ТО'
        verbose_name_plural = 'Техническое обслуживание'
        ordering = ['-maintenance_date', '-pk']

    def clean(self):
        if self.machine_id and self.service_company_id and self.machine.service_company_id != self.service_company_id:
            raise ValidationError({'service_company': 'Выберите сервисную компанию этой машины.'})

    def __str__(self):
        return f'ТО {self.machine} от {self.maintenance_date:%d.%m.%Y}'


class Claim(models.Model):
    failure_date = models.DateField('Дата отказа')
    operating_hours = models.PositiveIntegerField('Наработка, м/час')
    failure_node = reference('Узел отказа', 'failure')
    description = models.TextField('Описание отказа')
    recovery_method = reference('Способ восстановления', 'recovery')
    spare_parts = models.TextField('Используемые запасные части', blank=True)
    recovery_date = models.DateField('Дата восстановления', null=True, blank=True)
    machine = models.ForeignKey(Machine, verbose_name='Машина', on_delete=models.PROTECT, related_name='claims')
    service_company = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Сервисная компания',
                                        on_delete=models.PROTECT, limit_choices_to={'groups__name': 'Сервисная организация'})

    class Meta:
        verbose_name = 'Рекламация'
        verbose_name_plural = 'Рекламации'
        ordering = ['-failure_date', '-pk']

    @property
    def downtime(self):
        if self.recovery_date:
            return (self.recovery_date - self.failure_date).days
        return None

    def clean(self):
        if self.recovery_date and self.failure_date and self.recovery_date < self.failure_date:
            raise ValidationError({'recovery_date': 'Дата восстановления не может быть раньше даты отказа.'})
        if self.machine_id and self.service_company_id and self.machine.service_company_id != self.service_company_id:
            raise ValidationError({'service_company': 'Выберите сервисную компанию этой машины.'})

    def __str__(self):
        return f'Рекламация {self.machine} от {self.failure_date:%d.%m.%Y}'
