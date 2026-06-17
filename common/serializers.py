"""Shared serializer base classes."""

from rest_framework import serializers


class StrictFieldsModelSerializer(serializers.ModelSerializer):
    """ModelSerializer that rejects unknown keys in the input payload.

    DRF silently ignores unexpected fields by default, which hides typos and
    allows callers to send fields that are read-only or simply do not exist.
    This base raises a validation error instead.
    """

    def to_internal_value(self, data):
        if isinstance(data, dict):
            writable_fields = {name for name, field in self.fields.items() if not field.read_only}
            unknown = set(data) - writable_fields
            if unknown:
                raise serializers.ValidationError(
                    {field: "Unknown field." for field in sorted(unknown)}
                )
        return super().to_internal_value(data)
