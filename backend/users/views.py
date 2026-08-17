from rest_framework import generics, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import ProfileSerializer
from rest_framework.views import APIView
from .serializers import ChangePasswordSerializer


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'old_password': 'Incorrect password.'}, status=400)

        user.set_password(serializer.validated_data['new_password'])
        user.must_change_password = False
        user.save()
        return Response({'detail': 'Password changed successfully.'})

class ProfileView(generics.RetrieveUpdateAPIView):
    """
    Authenticated users can view/update their OWN profile only.
    get_object() is overridden to always return request.user —
    this is what prevents User A from editing User B's profile.
    """
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    """
    Blacklists the refresh token so it can never be used again.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Logged out successfully."}, status=205)
        except Exception:
            return Response({"detail": "Invalid token."}, status=400)