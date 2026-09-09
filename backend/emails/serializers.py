from rest_framework import serializers


class EmailSerializer(serializers.Serializer):
    subject = serializers.CharField()
    message = serializers.CharField()
    recipients = serializers.ListField(
        child=serializers.EmailField(),
        allow_empty=False
    )
    html_message = serializers.CharField(required=False, allow_blank=True)

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        if isinstance(ret.get('recipients'), str):
            ret['recipients'] = [email.strip() for email in ret['recipients'].split(',') if email.strip()]
        return ret
