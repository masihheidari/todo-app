from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from website.models import Task


class AdminTaskSerializer(ModelSerializer):
    """Full access: admins can edit everything except the author.
    Also used for list/retrieve/create for every role."""

    class Meta:
        model = Task
        fields = [
            "id",
            "author",
            "title",
            "content",
            "is_done",
            "created_date",
            "finished_date",
        ]
        # Author is set from request.user in perform_create
        read_only_fields = ["author"]


class TeacherTaskSerializer(ModelSerializer):
    """Teachers can edit title/content but must not change is_done."""

    class Meta:
        model = Task
        fields = [
            "author",
            "title",
            "content",
            "is_done",
            "created_date",
            "finished_date",
        ]
        read_only_fields = ["author", "is_done"]

    def validate(self, attrs):
        # read_only fields are ignored silently, so we check the raw request
        # data to return an explicit error when is_done is sent
        request = self.context.get("request")
        if request and "is_done" in request.data:
            raise serializers.ValidationError({"is_done": "teachers cant change that"})
        return attrs


class StudentTaskSerializer(ModelSerializer):
    """Students can only toggle is_done; everything else is read-only."""

    class Meta:
        model = Task
        fields = [
            "author",
            "title",
            "content",
            "is_done",
            "created_date",
            "finished_date",
        ]
        read_only_fields = [
            "author",
            "title",
            "content",
            "created_date",
            "finished_date",
        ]
