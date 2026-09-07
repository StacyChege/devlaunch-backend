from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['full_name', 'email', 'password', 'confirm_password']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError(
                {'confirm_password': 'Passwords do not match'}
            )
        validate_password(data['password'])
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            password=validated_data['password'],
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'role', 'is_verified']
        read_only_fields = ['id', 'role', 'is_verified']


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Self-service profile edits. Email and role are not changeable here."""

    class Meta:
        model = User
        fields = ['full_name']

    def validate_full_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Full name cannot be empty.')
        return value


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value

    def validate_new_password(self, value):
        validate_password(value, user=self.context['request'].user)
        return value

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user


class EmailSerializer(serializers.Serializer):
    """Shared by resend-verification and password-reset request."""
    email = serializers.EmailField()


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    def validate_new_password(self, value):
        validate_password(value)
        return value
