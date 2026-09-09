from rest_framework import serializers
from .models import Sponsor
from .models import Student


class SponsorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Sponsor
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create only fields
        if self.instance:
            self.fields['email'].read_only = True


class StudentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Student
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create only fields
        if self.instance:
            self.fields['email'].read_only = True
