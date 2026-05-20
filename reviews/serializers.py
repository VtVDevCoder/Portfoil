from .models import FeedbackBatch, FeedbackItem
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.validators import UniqueValidator


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class FeedbackItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackItem
        fields = ['id', 'raw_text', 'status']


class FeedbackBatchSerializer(serializers.ModelSerializer):
    items = FeedbackItemSerializer(many=True, read_only=True)
    raw_text_list = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        help_text="Lista de strings de feedbacks para processar em lote"
    )

    class Meta:
        model = FeedbackBatch
        fields = ['id', 'user', 'is_processed',
                  'created_at', 'items', 'raw_text_list']
        read_only_fields = ['user', 'is_processed', 'created_at']

    def create(self, validated_data):
        raw_text_list = validated_data.pop('raw_text_list')
        user = self.context['request'].user

        # Cria o lote principal
        batch = FeedbackBatch.objects.create(user=user, is_processed=False)

        # Cria todos os itens pendentes vinculados a este lote
        for text in raw_text_list:
            FeedbackItem.objects.create(
                batch=batch, raw_text=text, status='PENDING')

        return batch
