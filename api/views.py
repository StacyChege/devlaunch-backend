from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .emails import (
    read_email_verification_token,
    send_password_reset_email,
    send_verification_email,
    send_welcome_email,
)
from .serializers import (
    ChangePasswordSerializer,
    EmailSerializer,
    PasswordResetConfirmSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserSerializer,
    VerifyEmailSerializer,
)

User = get_user_model()


def token_payload(user):
    """Standard auth response: user + access/refresh JWTs."""
    refresh = RefreshToken.for_user(user)
    return {
        'user': UserSerializer(user).data,
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        send_verification_email(user)
        send_welcome_email(user)

        # No tokens yet — the dashboard is gated behind email verification.
        return Response(
            {
                'message': 'Account created. Check your email to verify your address.',
                'email': user.email,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Email and password are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=email, password=password)

        if not user:
            return Response(
                {'error': 'Invalid email or password'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_verified:
            return Response(
                {
                    'error': 'Please verify your email before signing in.',
                    'code': 'email_not_verified',
                    'email': user.email,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(token_payload(user))


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = read_email_verification_token(serializer.validated_data['token'])
        if not user_id:
            return Response(
                {'error': 'This verification link is invalid or has expired.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Account no longer exists.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.is_verified:
            user.is_verified = True
            user.save(update_fields=['is_verified'])

        # Verifying also signs the user in.
        return Response(token_payload(user))


class ResendVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.filter(
            email__iexact=serializer.validated_data['email']
        ).first()
        if user and not user.is_verified:
            send_verification_email(user)

        # Don't reveal whether the address is registered.
        return Response(
            {'message': 'If that address needs verification, a new link is on its way.'}
        )


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.filter(
            email__iexact=serializer.validated_data['email']
        ).first()
        if user:
            send_password_reset_email(user)

        return Response(
            {'message': 'If that account exists, a reset link has been sent.'}
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            uid = force_str(urlsafe_base64_decode(data['uid']))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(
            user, data['token']
        ):
            return Response(
                {'error': 'This reset link is invalid or has expired.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(data['new_password'])
        user.save(update_fields=['password'])
        return Response({'message': 'Password updated. You can now sign in.'})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Password updated.'})
