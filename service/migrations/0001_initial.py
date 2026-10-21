import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Directory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[('machine', 'Модель техники'), ('engine', 'Модель двигателя'), ('transmission', 'Модель трансмиссии'), ('drive_axle', 'Модель ведущего моста'), ('steer_axle', 'Модель управляемого моста'), ('maintenance', 'Вид ТО'), ('organization', 'Организация, проводившая ТО'), ('failure', 'Узел отказа'), ('recovery', 'Способ восстановления')], max_length=20, verbose_name='Название справочника')),
                ('name', models.CharField(max_length=200, verbose_name='Название')),
                ('description', models.TextField(verbose_name='Описание')),
            ],
            options={
                'verbose_name': 'Справочник',
                'verbose_name_plural': 'Справочники',
                'ordering': ['kind', 'name'],
                'constraints': [models.UniqueConstraint(fields=('kind', 'name'), name='unique_directory_item')],
            },
        ),
        migrations.CreateModel(
            name='Machine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('serial_number', models.CharField(max_length=100, unique=True, verbose_name='Зав. № машины')),
                ('engine_number', models.CharField(max_length=100, verbose_name='Зав. № двигателя')),
                ('transmission_number', models.CharField(max_length=100, verbose_name='Зав. № трансмиссии')),
                ('drive_axle_number', models.CharField(max_length=100, verbose_name='Зав. № ведущего моста')),
                ('steer_axle_number', models.CharField(max_length=100, verbose_name='Зав. № управляемого моста')),
                ('supply_contract', models.CharField(max_length=250, verbose_name='Договор поставки №, дата')),
                ('shipment_date', models.DateField(verbose_name='Дата отгрузки с завода')),
                ('consignee', models.CharField(max_length=250, verbose_name='Грузополучатель (конечный потребитель)')),
                ('delivery_address', models.TextField(verbose_name='Адрес поставки (эксплуатации)')),
                ('equipment', models.TextField(blank=True, verbose_name='Комплектация (доп. опции)')),
                ('client', models.ForeignKey(limit_choices_to={'groups__name': 'Клиент'}, on_delete=django.db.models.deletion.PROTECT, related_name='client_machines', to=settings.AUTH_USER_MODEL, verbose_name='Клиент')),
                ('drive_axle_model', models.ForeignKey(limit_choices_to={'kind': 'drive_axle'}, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='service.directory', verbose_name='Модель ведущего моста')),
                ('engine_model', models.ForeignKey(limit_choices_to={'kind': 'engine'}, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='service.directory', verbose_name='Модель двигателя')),
                ('machine_model', models.ForeignKey(limit_choices_to={'kind': 'machine'}, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='service.directory', verbose_name='Модель техники')),
                ('service_company', models.ForeignKey(limit_choices_to={'groups__name': 'Сервисная организация'}, on_delete=django.db.models.deletion.PROTECT, related_name='serviced_machines', to=settings.AUTH_USER_MODEL, verbose_name='Сервисная компания')),
                ('steer_axle_model', models.ForeignKey(limit_choices_to={'kind': 'steer_axle'}, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='service.directory', verbose_name='Модель управляемого моста')),
                ('transmission_model', models.ForeignKey(limit_choices_to={'kind': 'transmission'}, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='service.directory', verbose_name='Модель трансмиссии')),
            ],
            options={
                'verbose_name': 'Машина',
                'verbose_name_plural': 'Машины',
                'ordering': ['-shipment_date', 'serial_number'],
            },
        ),
        migrations.CreateModel(
            name='Claim',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('failure_date', models.DateField(verbose_name='Дата отказа')),
                ('operating_hours', models.PositiveIntegerField(verbose_name='Наработка, м/час')),
                ('description', models.TextField(verbose_name='Описание отказа')),
                ('spare_parts', models.TextField(blank=True, verbose_name='Используемые запасные части')),
                ('recovery_date', models.DateField(blank=True, null=True, verbose_name='Дата восстановления')),
                ('service_company', models.ForeignKey(limit_choices_to={'groups__name': 'Сервисная организация'}, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='Сервисная компания')),
                ('failure_node', models.ForeignKey(limit_choices_to={'kind': 'failure'}, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='service.directory', verbose_name='Узел отказа')),
                ('recovery_method', models.ForeignKey(limit_choices_to={'kind': 'recovery'}, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='service.directory', verbose_name='Способ восстановления')),
                ('machine', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='claims', to='service.machine', verbose_name='Машина')),
            ],
            options={
                'verbose_name': 'Рекламация',
                'verbose_name_plural': 'Рекламации',
                'ordering': ['-failure_date', '-pk'],
            },
        ),
        migrations.CreateModel(
            name='Maintenance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('maintenance_date', models.DateField(verbose_name='Дата проведения ТО')),
                ('operating_hours', models.PositiveIntegerField(verbose_name='Наработка, м/час')),
                ('work_order_number', models.CharField(max_length=100, verbose_name='№ заказ-наряда')),
                ('work_order_date', models.DateField(verbose_name='Дата заказ-наряда')),
                ('machine', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='maintenances', to='service.machine', verbose_name='Машина')),
                ('maintenance_type', models.ForeignKey(limit_choices_to={'kind': 'maintenance'}, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='service.directory', verbose_name='Вид ТО')),
                ('organization', models.ForeignKey(limit_choices_to={'kind': 'organization'}, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='service.directory', verbose_name='Организация, проводившая ТО')),
                ('service_company', models.ForeignKey(limit_choices_to={'groups__name': 'Сервисная организация'}, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='Сервисная компания')),
            ],
            options={
                'verbose_name': 'ТО',
                'verbose_name_plural': 'Техническое обслуживание',
                'ordering': ['-maintenance_date', '-pk'],
            },
        ),
    ]
