from rest_framework import serializers, viewsets
from rest_framework.exceptions import ValidationError
from .models import Directory, Machine, Maintenance, Claim
from .tables import scoped_records, filter_records


class DirectorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Directory
        fields = ['id', 'kind', 'name', 'description']


class MachineSerializer(serializers.ModelSerializer):
    machine_model = DirectorySerializer()
    engine_model = DirectorySerializer()
    transmission_model = DirectorySerializer()
    drive_axle_model = DirectorySerializer()
    steer_axle_model = DirectorySerializer()

    class Meta:
        model = Machine
        fields = '__all__'


class MaintenanceSerializer(serializers.ModelSerializer):
    maintenance_type = DirectorySerializer()
    organization = DirectorySerializer()
    machine_number = serializers.CharField(source='machine.serial_number')

    class Meta:
        model = Maintenance
        fields = '__all__'


class ClaimSerializer(serializers.ModelSerializer):
    failure_node = DirectorySerializer()
    recovery_method = DirectorySerializer()
    downtime = serializers.IntegerField(read_only=True, allow_null=True)
    machine_number = serializers.CharField(source='machine.serial_number')

    class Meta:
        model = Claim
        fields = '__all__'


class RecordViewSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        qs, form = filter_records(scoped_records(self.request.user, self.section), self.section, self.request.query_params)
        if not form.is_valid():
            raise ValidationError(form.errors)
        return qs


class MachineViewSet(RecordViewSet):
    section = 'machines'
    serializer_class = MachineSerializer


class MaintenanceViewSet(RecordViewSet):
    section = 'maintenances'
    serializer_class = MaintenanceSerializer


class ClaimViewSet(RecordViewSet):
    section = 'claims'
    serializer_class = ClaimSerializer
