"""General mixins."""
from django.conf import settings
from rest_framework import serializers
from rest_framework.decorators import detail_route
from rest_framework.response import Response


MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class ArchiveSerializer(serializers.Serializer):
    """Serializer for archive endpoints."""

    reason = serializers.CharField(max_length=MAX_LENGTH)


class ArchivableViewSetMixin:
    """To be used with archivable models."""

    @detail_route(methods=['post'])
    def archive(self, request, pk):
        """Archive the object."""
        serializer = ArchiveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data['reason']

        obj = self.get_object()
        obj.archive(user=request.user, reason=reason)
        serializer = self.get_serializer_class()(obj)
        return Response(data=serializer.data)

    # TODO: Remove GET method from this route
    @detail_route(methods=['post'])
    def unarchive(self, request, pk):
        """Unarchive the object."""
        obj = self.get_object()
        obj.unarchive()
        serializer = self.get_serializer_class()(obj)
        return Response(data=serializer.data)
