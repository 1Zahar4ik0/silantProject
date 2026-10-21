from datetime import date
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, Client
from .models import Directory, Machine, Maintenance, Claim
from .forms import MaintenanceForm


class AccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('setup_roles', verbosity=0)
        cls.users = {}
        for username, group in [('client', 'Клиент'), ('other', 'Клиент'), ('service', 'Сервисная организация'),
                                ('other_service', 'Сервисная организация'), ('manager', 'Менеджер')]:
            user = User.objects.create_user(username=username, password='Test-password-123')
            user.groups.add(Group.objects.get(name=group))
            cls.users[username] = user
        cls.items = {kind: Directory.objects.create(kind=kind, name=label, description='Описание: ' + label)
                     for kind, label in Directory.Kind.choices}
        common = dict(machine_model=cls.items['machine'], engine_model=cls.items['engine'], engine_number='E1',
                      transmission_model=cls.items['transmission'], transmission_number='T1',
                      drive_axle_model=cls.items['drive_axle'], drive_axle_number='D1',
                      steer_axle_model=cls.items['steer_axle'], steer_axle_number='S1',
                      supply_contract='PRIVATE-CONTRACT', consignee='PRIVATE-CONSIGNEE',
                      delivery_address='PRIVATE-ADDRESS', equipment='PRIVATE-EQUIPMENT')
        cls.machine = Machine.objects.create(serial_number='0001', shipment_date=date(2022, 1, 1),
            client=cls.users['client'], service_company=cls.users['service'], **common)
        cls.other_machine = Machine.objects.create(serial_number='0002', shipment_date=date(2022, 2, 1),
            client=cls.users['other'], service_company=cls.users['other_service'], **common)
        cls.records = {}
        for machine in [cls.machine, cls.other_machine]:
            maintenance = Maintenance.objects.create(machine=machine, maintenance_type=cls.items['maintenance'],
                maintenance_date=date(2022, 3, 1), operating_hours=50, work_order_number='TO1',
                work_order_date=date(2022, 2, 28), organization=cls.items['organization'], service_company=machine.service_company)
            claim = Claim.objects.create(machine=machine, failure_date=date(2022, 4, 1), operating_hours=70,
                failure_node=cls.items['failure'], description='Стук', recovery_method=cls.items['recovery'],
                recovery_date=date(2022, 4, 5), service_company=machine.service_company)
            cls.records[machine.pk] = {'machines': machine, 'maintenances': maintenance, 'claims': claim}

    def test_guest_sees_only_ten_fields(self):
        for url in ['/?serial_number=0001', '/public/machines/0001/']:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, '0001')
            for secret in ['PRIVATE-CONTRACT', 'PRIVATE-CONSIGNEE', 'PRIVATE-ADDRESS', 'PRIVATE-EQUIPMENT']:
                self.assertNotContains(response, secret)
        self.assertEqual(len(self.client.get('/?serial_number=0001').context['columns']), 10)

    def test_guest_empty_and_missing_search(self):
        self.assertContains(self.client.get('/'), 'Введите заводской номер')
        self.assertContains(self.client.get('/?serial_number=unknown'), 'нет в системе')

    def test_guest_cannot_read_private_records_or_api(self):
        for section in ['machines', 'maintenances', 'claims']:
            self.assertEqual(self.client.get(f'/records/{section}/').status_code, 302)
            self.assertEqual(self.client.get(f'/api/{section}/').status_code, 403)

    def test_object_isolation_in_pages_and_api(self):
        for username in ['client', 'service']:
            self.client.force_login(self.users[username])
            for section in ['machines', 'maintenances', 'claims']:
                foreign = self.records[self.other_machine.pk][section]
                self.assertEqual(self.client.get(f'/records/{section}/{foreign.pk}/').status_code, 404)
                self.assertEqual(self.client.get(f'/api/{section}/{foreign.pk}/').status_code, 404)
                response = self.client.get(f'/api/{section}/').json()
                self.assertEqual(response['count'], 1)

    def test_manager_can_see_all(self):
        self.client.force_login(self.users['manager'])
        for section in ['machines', 'maintenances', 'claims']:
            self.assertEqual(self.client.get(f'/api/{section}/').json()['count'], 2)
            self.assertEqual(self.client.get(f'/records/{section}/').status_code, 200)

    def test_edit_matrix(self):
        expected = {'client': {'maintenances'}, 'service': {'maintenances', 'claims'},
                    'manager': {'machines', 'maintenances', 'claims'}}
        for username, allowed in expected.items():
            self.client.force_login(self.users[username])
            for section in ['machines', 'maintenances', 'claims']:
                record = self.records[self.machine.pk][section]
                for url in [f'/records/{section}/add/', f'/records/{section}/{record.pk}/edit/']:
                    self.assertEqual(self.client.get(url).status_code, 200 if section in allowed else 403)
                    self.assertEqual(self.client.post(url, {}).status_code, 200 if section in allowed else 403)

    def test_client_can_save_maintenance_and_company_is_not_spoofable(self):
        self.client.force_login(self.users['client'])
        response = self.client.post('/records/maintenances/add/', self.maintenance_data(self.machine))
        self.assertEqual(response.status_code, 302)
        record = Maintenance.objects.get(work_order_number='NEW')
        self.assertEqual(record.service_company, self.users['service'])

    def maintenance_data(self, machine):
        return {'machine': machine.pk, 'maintenance_type': self.items['maintenance'].pk,
                'maintenance_date': '2022-06-01', 'operating_hours': 200, 'work_order_number': 'NEW',
                'work_order_date': '2022-05-30', 'organization': self.items['organization'].pk,
                'service_company': self.users['other_service'].pk}

    def test_forged_machine_rejected(self):
        self.client.force_login(self.users['client'])
        response = self.client.post('/records/maintenances/add/', self.maintenance_data(self.other_machine))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Maintenance.objects.filter(work_order_number='NEW').exists())

    def test_foreign_edit_rejected(self):
        self.client.force_login(self.users['service'])
        foreign = self.records[self.other_machine.pk]['claims']
        self.assertEqual(self.client.post(f'/records/claims/{foreign.pk}/edit/', {}).status_code, 404)

    def test_negative_hours_rejected(self):
        data = self.maintenance_data(self.machine)
        data['operating_hours'] = -1
        form = MaintenanceForm(data, user=self.users['client'])
        self.assertFalse(form.is_valid())
        self.assertIn('operating_hours', form.errors)

    def test_downtime_and_invalid_dates(self):
        claim = self.records[self.machine.pk]['claims']
        self.assertEqual(claim.downtime, 4)
        claim.recovery_date = None
        self.assertIsNone(claim.downtime)
        claim.recovery_date = date(2022, 3, 31)
        with self.assertRaises(ValidationError):
            claim.full_clean()

    def test_dictionary_description_in_details(self):
        self.client.force_login(self.users['client'])
        for section in ['machines', 'maintenances', 'claims']:
            record = self.records[self.machine.pk][section]
            self.assertContains(self.client.get(f'/records/{section}/{record.pk}/'), 'Описание:')

    def test_filters_and_sorting(self):
        self.client.force_login(self.users['manager'])
        self.assertEqual(self.client.get('/api/machines/').json()['results'][0]['serial_number'], '0002')
        self.assertEqual(self.client.get('/api/machines/?order=asc').json()['results'][0]['serial_number'], '0001')
        url = f'/api/maintenances/?machine={self.machine.pk}'
        self.assertEqual(self.client.get(url).json()['count'], 1)
        for section, field, item in [('machines', 'engine_model', 'engine'), ('maintenances', 'maintenance_type', 'maintenance'),
                                      ('claims', 'failure_node', 'failure')]:
            self.assertEqual(self.client.get(f'/api/{section}/?{field}={self.items[item].pk}').json()['count'], 2)
        self.assertEqual(self.client.get('/api/machines/?engine_model=wrong').status_code, 400)

    def test_only_manager_edits_directories(self):
        self.client.force_login(self.users['client'])
        self.assertEqual(self.client.get('/directories/').status_code, 403)
        self.assertEqual(self.client.post('/directories/add/', {}).status_code, 403)
        self.client.force_login(self.users['manager'])
        self.assertEqual(self.client.post('/directories/add/', {'kind': 'engine', 'name': 'New', 'description': 'Описание'}).status_code, 302)

    def test_registration_and_password_changes_closed(self):
        count = User.objects.count()
        self.assertContains(self.client.get('/accounts/signup/'), 'Регистрация закрыта')
        self.client.post('/accounts/signup/', {'username': 'intruder', 'password1': 'Secret123!', 'password2': 'Secret123!'})
        self.assertEqual(User.objects.count(), count)
        for path in ['password/change', 'password/reset', 'email']:
            self.assertEqual(self.client.get(f'/accounts/{path}/').status_code, 404)

    def test_login_logout(self):
        response = self.client.post('/accounts/login/', {'username': 'client', 'password': 'Test-password-123'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get('/records/machines/').status_code, 200)
        self.assertEqual(self.client.get('/accounts/logout/').status_code, 405)
        self.assertEqual(self.client.post('/accounts/logout/').status_code, 302)

    def test_csrf_is_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.users['manager'])
        self.assertEqual(client.post('/directories/add/', {'kind': 'engine', 'name': 'X', 'description': 'X'}).status_code, 403)

    def test_user_without_role_has_no_records(self):
        user = User.objects.create_user(username='no_role')
        self.client.force_login(user)
        self.assertEqual(self.client.get('/api/machines/').json()['count'], 0)
        self.assertEqual(self.client.get('/records/maintenances/add/').status_code, 403)

    def test_api_is_read_only(self):
        self.client.force_login(self.users['manager'])
        self.assertEqual(self.client.post('/api/machines/', {}).status_code, 405)

    def test_staff_flag_does_not_bypass_machine_scope(self):
        user = self.users['client']
        user.is_staff = True
        user.save()
        self.client.force_login(user)
        self.assertEqual(self.client.get('/admin/service/machine/').status_code, 403)

    def test_service_can_create_claim(self):
        self.client.force_login(self.users['service'])
        response = self.client.post('/records/claims/add/', {
            'machine': self.machine.pk, 'failure_date': '2022-07-01', 'operating_hours': 300,
            'failure_node': self.items['failure'].pk, 'description': 'Новая рекламация',
            'recovery_method': self.items['recovery'].pk, 'spare_parts': '', 'recovery_date': '2022-07-04',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Claim.objects.get(description='Новая рекламация').downtime, 3)

    def test_manager_can_create_machine(self):
        self.client.force_login(self.users['manager'])
        from django.forms.models import model_to_dict
        data = model_to_dict(self.machine)
        data['serial_number'] = '0003'
        response = self.client.post('/records/machines/add/', data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Machine.objects.filter(serial_number='0003').exists())

    def test_wrong_directory_type_rejected(self):
        data = self.maintenance_data(self.machine)
        data['maintenance_type'] = self.items['engine'].pk
        form = MaintenanceForm(data, user=self.users['client'])
        self.assertFalse(form.is_valid())
        self.assertIn('maintenance_type', form.errors)
