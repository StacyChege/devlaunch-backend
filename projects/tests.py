from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from templates.models import Template
from .models import Project

User = get_user_model()


class ProjectApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='dev@example.com', full_name='Dev', password='Str0ngPass!23'
        )
        self.user.is_verified = True
        self.user.save(update_fields=['is_verified'])
        self.other = User.objects.create_user(
            email='other@example.com', full_name='Other', password='Str0ngPass!23'
        )
        self.template = Template.objects.create(
            name='Solo Portfolio', category=Template.PORTFOLIO,
            description='Clean portfolio.',
        )
        self.client.force_authenticate(self.user)

    def test_requires_auth(self):
        self.client.force_authenticate(None)
        self.assertEqual(
            self.client.get('/api/projects/').status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_create_from_template_assigns_slug_and_draft_status(self):
        res = self.client.post(
            '/api/projects/', {'template_id': self.template.id}, format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['status'], 'DRAFT')
        self.assertTrue(res.data['slug'])
        self.assertIsNone(res.data['live_url'])
        self.assertTrue(res.data['preview_url'].endswith('.devlaunch.app'))
        self.assertEqual(res.data['template_name'], 'Solo Portfolio')

    def test_create_requires_template_id(self):
        res = self.client.post('/api/projects/', {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_rejects_unknown_template(self):
        res = self.client.post(
            '/api/projects/', {'template_id': 9999}, format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_only_returns_own_projects(self):
        Project.objects.create(developer=self.user, template=self.template, name='Mine')
        Project.objects.create(developer=self.other, template=self.template, name='Theirs')
        res = self.client.get('/api/projects/')
        self.assertEqual([p['name'] for p in res.data], ['Mine'])

    def test_patch_updates_name_and_customisation(self):
        project = Project.objects.create(
            developer=self.user, template=self.template, name='Draft'
        )
        res = self.client.patch(
            f'/api/projects/{project.id}/',
            {'name': 'Renamed', 'customisation_data': {'tagline': 'hi'}},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        project.refresh_from_db()
        self.assertEqual(project.name, 'Renamed')
        self.assertEqual(project.customisation_data['tagline'], 'hi')

    def test_cannot_touch_another_users_project(self):
        project = Project.objects.create(
            developer=self.other, template=self.template, name='Theirs'
        )
        self.assertEqual(
            self.client.get(f'/api/projects/{project.id}/').status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.delete(f'/api/projects/{project.id}/').status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_delete_removes_project(self):
        project = Project.objects.create(
            developer=self.user, template=self.template, name='Draft'
        )
        res = self.client.delete(f'/api/projects/{project.id}/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Project.objects.filter(pk=project.id).exists())

    def test_stats_counts_projects_and_deployments(self):
        Project.objects.create(developer=self.user, template=self.template, name='A')
        Project.objects.create(
            developer=self.user, template=self.template, name='B',
            status=Project.STATUS_DEPLOYED,
        )
        res = self.client.get('/api/projects/stats/')
        self.assertEqual(res.data['total_projects'], 2)
        self.assertEqual(res.data['deployed_sites'], 1)
        self.assertEqual(len(res.data['recent_projects']), 2)

    def test_live_url_appears_once_deployed(self):
        project = Project.objects.create(
            developer=self.user, template=self.template, name='A',
            status=Project.STATUS_DEPLOYED,
        )
        res = self.client.get(f'/api/projects/{project.id}/')
        self.assertEqual(res.data['live_url'], res.data['preview_url'])
