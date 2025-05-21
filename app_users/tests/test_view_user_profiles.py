from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from app_users.models import UserProfiles
from rest_framework_simplejwt.tokens import RefreshToken
import uuid

CustomUserModel = get_user_model()


class UserProfileViewsTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # User 1 with some profiles
        cls.user1 = CustomUserModel.objects.create_user(
            username="profileuser1",
            email="profile1@example.com",
            password="Pass123!",
            is_active=True,
            is_email_verified=True,
        )
        cls.profile1_user1 = UserProfiles.objects.create(user=cls.user1, profile_name="Profile1.1")
        cls.profile2_user1 = UserProfiles.objects.create(user=cls.user1, profile_name="Profile1.2", is_kid=True)

        # User 2 (will be used to test permissions)
        cls.user2 = CustomUserModel.objects.create_user(
            username="profileuser2",
            email="profile2@example.com",
            password="Pass456!",
            is_active=True,
            is_email_verified=True,
        )
        cls.profile1_user2 = UserProfiles.objects.create(user=cls.user2, profile_name="Profile2.1")

    def setUp(self):
        self.client = APIClient()
        self.list_create_url = reverse("user_profile_list_create")  # /me/profiles/

    def _authenticate_user(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

    # --- UserProfileListCreateView Tests ---

    def test_list_user_profiles_authenticated(self):
        self._authenticate_user(self.user1)
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # User1 has 2 profiles
        profile_names = [p["profile_name"] for p in response.data]
        self.assertIn("Profile1.1", profile_names)
        self.assertIn("Profile1.2", profile_names)

    def test_list_user_profiles_unauthenticated(self):
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_user_profile_authenticated(self):
        self._authenticate_user(self.user1)
        initial_profile_count = UserProfiles.objects.filter(user=self.user1).count()
        data = {"profile_name": "New Profile 1.3", "preferred_language": "de"}
        response = self.client.post(self.list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserProfiles.objects.filter(user=self.user1).count(), initial_profile_count + 1)
        self.assertTrue(UserProfiles.objects.filter(user=self.user1, profile_name="New Profile 1.3").exists())
        self.assertEqual(response.data["profile_name"], "New Profile 1.3")
        self.assertEqual(response.data["preferred_language"], "de")

    def test_create_user_profile_unauthenticated(self):
        data = {"profile_name": "Attempt Profile"}
        response = self.client.post(self.list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_user_profile_max_limit(self):
        self._authenticate_user(self.user1)
        # User1 already has 2 profiles. Create 2 more to reach limit of 4.
        UserProfiles.objects.create(user=self.user1, profile_name="LimitTest1")
        UserProfiles.objects.create(user=self.user1, profile_name="LimitTest2")
        self.assertEqual(UserProfiles.objects.filter(user=self.user1).count(), 4)

        data = {"profile_name": "OverLimitProfile"}
        response = self.client.post(self.list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)  # Default error key for ValidationError
        self.assertEqual(str(response.data["detail"]), "You can only have a maximum of 4 profiles.")
        self.assertEqual(UserProfiles.objects.filter(user=self.user1).count(), 4)  # Should not have created

    def test_create_user_profile_missing_profile_name(self):
        self._authenticate_user(self.user1)
        data = {"preferred_language": "en"}
        response = self.client.post(self.list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("profile_name", response.data)
        self.assertEqual(response.data["profile_name"][0].code, "required")

    # --- UserProfileDetailView Tests ---

    def _get_detail_url(self, profile_id):
        return reverse("user_profile_detail", kwargs={"profile_id": profile_id})

    def test_get_profile_detail_authenticated_owner(self):
        self._authenticate_user(self.user1)
        url = self._get_detail_url(self.profile1_user1.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["profile_name"], self.profile1_user1.profile_name)
        self.assertEqual(response.data["id"], str(self.profile1_user1.id))

    def test_get_profile_detail_unauthenticated(self):
        url = self._get_detail_url(self.profile1_user1.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profile_detail_authenticated_not_owner(self):
        self._authenticate_user(self.user2)  # Authenticate as user2
        url = self._get_detail_url(self.profile1_user1.id)  # Try to access user1's profile
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  # get_object_or_404 due to queryset filtering

    def test_update_profile_detail_authenticated_owner(self):
        self._authenticate_user(self.user1)
        url = self._get_detail_url(self.profile1_user1.id)
        update_data = {"profile_name": "Updated Name 1.1", "is_kid": True}
        response = self.client.patch(url, update_data, format="json")  # PATCH for partial update
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile1_user1.refresh_from_db()
        self.assertEqual(self.profile1_user1.profile_name, "Updated Name 1.1")
        self.assertTrue(self.profile1_user1.is_kid)
        self.assertEqual(response.data["profile_name"], "Updated Name 1.1")

    def test_update_profile_detail_put_requires_all_fields_or_partial_true(self):
        self._authenticate_user(self.user1)
        url = self._get_detail_url(self.profile1_user1.id)
        # PUT usually requires all fields unless serializer is partial=True by default for PUT
        # or the view explicitly handles it. Generic views with DRF handle PATCH for partial.
        update_data = {"profile_name": "PUT Update Name"}  # Missing other fields
        response = self.client.put(url, update_data, format="json")
        if response.status_code == status.HTTP_400_BAD_REQUEST:  # Expected if not partial
            for field in ["picture", "is_kid", "preferred_language", "age_limit"]:
                if field not in update_data:  # Check only for fields not provided
                    self.assertIn(
                        field,
                        response.data,
                        f"{field} should be required for PUT or serializer is not handling partial PUT correctly",
                    )
        else:
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.profile1_user1.refresh_from_db()
            self.assertEqual(self.profile1_user1.profile_name, "PUT Update Name")

    def test_update_profile_detail_unauthenticated(self):
        url = self._get_detail_url(self.profile1_user1.id)
        update_data = {"profile_name": "Attempt Update"}
        response = self.client.patch(url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile_detail_not_owner(self):
        self._authenticate_user(self.user2)
        url = self._get_detail_url(self.profile1_user1.id)
        update_data = {"profile_name": "Malicious Update"}
        response = self.client.patch(url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_profile_detail_authenticated_owner(self):
        self._authenticate_user(self.user1)
        profile_to_delete_id = self.profile2_user1.id
        url = self._get_detail_url(profile_to_delete_id)
        initial_count = UserProfiles.objects.filter(user=self.user1).count()
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(UserProfiles.objects.filter(user=self.user1).count(), initial_count - 1)
        self.assertFalse(UserProfiles.objects.filter(id=profile_to_delete_id).exists())

    def test_delete_profile_detail_unauthenticated(self):
        url = self._get_detail_url(self.profile2_user1.id)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_profile_detail_not_owner(self):
        self._authenticate_user(self.user2)
        url = self._get_detail_url(self.profile2_user1.id)  # user1's profile
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(UserProfiles.objects.filter(id=self.profile2_user1.id).exists())  # Should not be deleted
