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

    def test_live_url_is_null_for_a_draft(self):
        project = Project.objects.create(
            developer=self.user, template=self.template, name='A',
        )
        res = self.client.get(f'/api/projects/{project.id}/')
        self.assertIsNone(res.data['live_url'])

    def test_live_url_resolves_to_the_sites_path_once_deployed(self):
        # Flipping status directly (no real Deployment) is enough to prove
        # the serializer's own gating logic — DeploymentTests below covers
        # the real pipeline setting this status.
        project = Project.objects.create(
            developer=self.user, template=self.template, name='A',
            status=Project.STATUS_DEPLOYED,
        )
        res = self.client.get(f'/api/projects/{project.id}/')
        self.assertTrue(res.data['live_url'].endswith(f'/sites/{project.slug}/'))
        self.assertNotEqual(res.data['live_url'], res.data['preview_url'])


class DeploymentTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='dev@example.com', full_name='Dev', password='Str0ngPass!23'
        )
        self.user.is_verified = True
        self.user.save(update_fields=['is_verified'])
        self.other = User.objects.create_user(
            email='other@example.com', full_name='Other', password='Str0ngPass!23'
        )
        # Real source — see template_sources/solo-portfolio.
        self.deployable = Template.objects.create(
            name='Solo Portfolio', category=Template.PORTFOLIO,
            description='Clean portfolio.', source_path='solo-portfolio',
        )
        self.undeployable = Template.objects.create(
            name='Agency One', category=Template.AGENCY,
            description='No source yet.', source_path='',
        )
        self.client.force_authenticate(self.user)

    def _create_project(self, template=None, name='My Site'):
        return Project.objects.create(
            developer=self.user, template=template or self.deployable, name=name
        )

    def test_deploy_renders_and_marks_project_live(self):
        project = self._create_project()
        project.customisation_data = {'tagline': 'Hello world'}
        project.save(update_fields=['customisation_data'])

        res = self.client.post(f'/api/projects/{project.id}/deploy/')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['deployment']['status'], 'SUCCESS')
        self.assertEqual(res.data['project']['status'], 'DEPLOYED')
        self.assertIsNotNone(res.data['project']['live_url'])

        project.refresh_from_db()
        self.assertEqual(project.status, Project.STATUS_DEPLOYED)
        deployment = project.deployments.first()
        self.assertEqual(deployment.status, 'SUCCESS')
        self.assertIn('Hello world', deployment.html)
        self.assertIn('My Site', deployment.html)

    def test_deploy_fails_gracefully_when_template_has_no_source(self):
        project = self._create_project(template=self.undeployable)

        res = self.client.post(f'/api/projects/{project.id}/deploy/')

        self.assertEqual(res.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(res.data['deployment']['status'], 'FAILED')
        self.assertTrue(res.data['deployment']['build_log'])
        self.assertEqual(res.data['project']['status'], 'FAILED')
        self.assertIsNone(res.data['project']['live_url'])

    def test_deploy_fails_when_project_has_no_template(self):
        project = self._create_project()
        project.template = None
        project.save(update_fields=['template'])

        res = self.client.post(f'/api/projects/{project.id}/deploy/')

        self.assertEqual(res.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn('no template', res.data['deployment']['build_log'].lower())

    def test_redeploy_creates_a_new_deployment_with_latest_customisation(self):
        project = self._create_project()

        self.client.post(f'/api/projects/{project.id}/deploy/')
        project.customisation_data = {'tagline': 'Second version'}
        project.save(update_fields=['customisation_data'])
        res = self.client.post(f'/api/projects/{project.id}/deploy/')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(project.deployments.count(), 2)
        self.assertIn('Second version', project.deployments.first().html)

    def test_deploy_requires_ownership(self):
        project = Project.objects.create(
            developer=self.other, template=self.deployable, name='Theirs'
        )
        res = self.client.post(f'/api/projects/{project.id}/deploy/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_rollback_republishes_the_previous_successful_deployment(self):
        project = self._create_project()
        project.customisation_data = {'tagline': 'v1'}
        project.save(update_fields=['customisation_data'])
        self.client.post(f'/api/projects/{project.id}/deploy/')

        project.customisation_data = {'tagline': 'v2'}
        project.save(update_fields=['customisation_data'])
        self.client.post(f'/api/projects/{project.id}/deploy/')

        res = self.client.post(f'/api/projects/{project.id}/rollback/')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['deployment']['is_rollback'])
        self.assertIn('v1', project.deployments.first().html)
        self.assertEqual(project.deployments.count(), 3)
        self.assertEqual(res.data['project']['status'], 'DEPLOYED')

    def test_rollback_without_two_successful_deploys_is_rejected(self):
        project = self._create_project()
        self.client.post(f'/api/projects/{project.id}/deploy/')  # only one

        res = self.client.post(f'/api/projects/{project.id}/rollback/')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_deployment_history_is_newest_first(self):
        project = self._create_project()
        self.client.post(f'/api/projects/{project.id}/deploy/')
        self.client.post(f'/api/projects/{project.id}/deploy/')

        res = self.client.get(f'/api/projects/{project.id}/deployments/')
        self.assertEqual(len(res.data), 2)
        self.assertTrue(res.data[0]['created_at'] >= res.data[1]['created_at'])


class SiteViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='dev@example.com', full_name='Dev', password='Str0ngPass!23'
        )
        self.template = Template.objects.create(
            name='Solo Portfolio', category=Template.PORTFOLIO,
            description='x', source_path='solo-portfolio',
        )
        self.project = Project.objects.create(
            developer=self.user, template=self.template, name='Jane Doe',
        )

    def test_404_before_any_deployment(self):
        res = self.client.get(f'/sites/{self.project.slug}/')
        self.assertEqual(res.status_code, 404)

    def test_404_for_unknown_slug(self):
        res = self.client.get('/sites/does-not-exist/')
        self.assertEqual(res.status_code, 404)

    def test_serves_the_latest_successful_deployment(self):
        self.client.force_authenticate(self.user)
        self.client.post(f'/api/projects/{self.project.id}/deploy/')

        res = self.client.get(f'/sites/{self.project.slug}/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'text/html')
        self.assertIn(b'Jane Doe', res.content)

    def test_is_public_no_auth_required(self):
        self.client.force_authenticate(self.user)
        self.client.post(f'/api/projects/{self.project.id}/deploy/')
        self.client.force_authenticate(None)

        res = self.client.get(f'/sites/{self.project.slug}/')
        self.assertEqual(res.status_code, 200)
