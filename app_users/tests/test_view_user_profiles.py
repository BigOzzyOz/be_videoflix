from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from app_users.models import UserProfiles
from rest_framework_simplejwt.tokens import RefreshToken

CustomUserModel = get_user_model()


class UserProfileViewsTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user1 = CustomUserModel.objects.create_user(
            username="profileuser1",
            email="profile1@example.com",
            password="Pass123!",
            is_active=True,
            is_email_verified=True,
        )
        cls.profile1_user1 = UserProfiles.objects.create(user=cls.user1, profile_name="Profile1.1")
        cls.profile2_user1 = UserProfiles.objects.create(user=cls.user1, profile_name="Profile1.2", is_kid=True)

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
        self.list_create_url = reverse("user_profile_list_create")

    def _authenticate_user(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

    def test_list_user_profiles_authenticated(self):
        self._authenticate_user(self.user1)
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
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
        UserProfiles.objects.create(user=self.user1, profile_name="LimitTest1")
        UserProfiles.objects.create(user=self.user1, profile_name="LimitTest2")
        self.assertEqual(UserProfiles.objects.filter(user=self.user1).count(), 4)

        data = {"profile_name": "OverLimitProfile"}
        response = self.client.post(self.list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        self.assertEqual(str(response.data["detail"]), "You can only have a maximum of 4 profiles.")
        self.assertEqual(UserProfiles.objects.filter(user=self.user1).count(), 4)

    def test_create_user_profile_missing_profile_name(self):
        self._authenticate_user(self.user1)
        data = {"preferred_language": "en"}
        response = self.client.post(self.list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("profile_name", response.data)
        self.assertEqual(response.data["profile_name"], ["This field is required."])

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
        self._authenticate_user(self.user2)
        url = self._get_detail_url(self.profile1_user1.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_profile_detail_authenticated_owner(self):
        self._authenticate_user(self.user1)
        url = self._get_detail_url(self.profile1_user1.id)
        update_data = {"profile_name": "Updated Name 1.1", "is_kid": True}
        response = self.client.patch(url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile1_user1.refresh_from_db()
        self.assertEqual(self.profile1_user1.profile_name, "Updated Name 1.1")
        self.assertTrue(self.profile1_user1.is_kid)
        self.assertEqual(response.data["profile_name"], "Updated Name 1.1")

    def test_update_profile_detail_put_requires_all_fields_or_partial_true(self):
        self._authenticate_user(self.user1)
        url = self._get_detail_url(self.profile1_user1.id)
        update_data = {"profile_name": "PUT Update Name"}
        response = self.client.put(url, update_data, format="json")
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            for field in ["picture", "is_kid", "preferred_language", "age_limit"]:
                if field not in update_data:
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
        url = self._get_detail_url(self.profile2_user1.id)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(UserProfiles.objects.filter(id=self.profile2_user1.id).exists())
