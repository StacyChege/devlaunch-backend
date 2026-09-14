from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from projects.deployment import run_deploy
from projects.models import Project
from templates.models import Template

User = get_user_model()


class AdminApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com', full_name='Admin', password='Str0ngPass!23'
        )
        self.admin.role = User.ADMIN
        self.admin.is_verified = True
        self.admin.save(update_fields=['role', 'is_verified'])

        self.dev = User.objects.create_user(
            email='dev@example.com', full_name='Dev', password='Str0ngPass!23'
        )
        self.template = Template.objects.create(
            name='Solo Portfolio', category=Template.PORTFOLIO, description='x'
        )
        Template.objects.create(
            name='Hidden', category=Template.BLOG, description='x', is_active=False
        )
        Project.objects.create(developer=self.dev, template=self.template, name='P1')
        Project.objects.create(
            developer=self.dev, template=self.template, name='P2',
            status=Project.STATUS_DEPLOYED,
        )

    # --- access control -----------------------------------------------------

    def test_developer_is_forbidden(self):
        self.client.force_authenticate(self.dev)
        for url in ['/api/admin/overview/', '/api/admin/users/', '/api/admin/templates/']:
            self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_is_unauthorized(self):
        self.assertEqual(
            self.client.get('/api/admin/overview/').status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    # --- overview ---------------------------------------------------------

    def test_overview_counts(self):
        self.client.force_authenticate(self.admin)
        res = self.client.get('/api/admin/overview/')
        self.assertEqual(res.data['total_users'], 2)
        self.assertEqual(res.data['developers'], 1)
        self.assertEqual(res.data['admins'], 1)
        self.assertEqual(res.data['total_projects'], 2)
        self.assertEqual(res.data['deployed_projects'], 1)
        self.assertEqual(res.data['total_templates'], 2)
        self.assertEqual(res.data['active_templates'], 1)

    # --- users ----------------------------------------------------------

    def test_user_list_has_project_counts(self):
        self.client.force_authenticate(self.admin)
        res = self.client.get('/api/admin/users/')
        row = next(r for r in res.data if r['email'] == 'dev@example.com')
        self.assertEqual(row['project_count'], 2)
        self.assertEqual(row['deployed_count'], 1)

    def test_user_list_search_and_role_filter(self):
        self.client.force_authenticate(self.admin)
        res = self.client.get('/api/admin/users/', {'search': 'dev@'})
        self.assertEqual([r['email'] for r in res.data], ['dev@example.com'])
        res = self.client.get('/api/admin/users/', {'role': 'ADMIN'})
        self.assertEqual([r['email'] for r in res.data], ['admin@example.com'])

    def test_suspend_and_reactivate_developer(self):
        self.client.force_authenticate(self.admin)
        res = self.client.post(
            f'/api/admin/users/{self.dev.id}/set-active/',
            {'is_active': False}, format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.dev.refresh_from_db()
        self.assertFalse(self.dev.is_active)

        res = self.client.post(
            f'/api/admin/users/{self.dev.id}/set-active/',
            {'is_active': True}, format='json',
        )
        self.dev.refresh_from_db()
        self.assertTrue(self.dev.is_active)

    def test_cannot_suspend_self(self):
        self.client.force_authenticate(self.admin)
        res = self.client.post(
            f'/api/admin/users/{self.admin.id}/set-active/',
            {'is_active': False}, format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_suspend_another_admin(self):
        other_admin = User.objects.create_user(
            email='a2@example.com', full_name='A2', password='Str0ngPass!23'
        )
        other_admin.role = User.ADMIN
        other_admin.save(update_fields=['role'])
        self.client.force_authenticate(self.admin)
        res = self.client.post(
            f'/api/admin/users/{other_admin.id}/set-active/',
            {'is_active': False}, format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_set_active_unknown_user_404(self):
        self.client.force_authenticate(self.admin)
        res = self.client.post(
            '/api/admin/users/9999/set-active/', {'is_active': False}, format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    # --- templates ------------------------------------------------------

    def test_template_list_includes_inactive(self):
        self.client.force_authenticate(self.admin)
        res = self.client.get('/api/admin/templates/')
        names = {t['name'] for t in res.data}
        self.assertIn('Hidden', names)

    def test_template_create(self):
        self.client.force_authenticate(self.admin)
        res = self.client.post(
            '/api/admin/templates/',
            {
                'name': 'New SaaS',
                'description': 'A SaaS template.',
                'category': 'SAAS',
                'tech_stack': 'React',
                'is_premium': True,
            },
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['slug'], 'new-saas')

    def test_template_toggle_active_and_delete(self):
        self.client.force_authenticate(self.admin)
        res = self.client.patch(
            f'/api/admin/templates/{self.template.id}/',
            {'is_active': False}, format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.template.refresh_from_db()
        self.assertFalse(self.template.is_active)

        res = self.client.delete(f'/api/admin/templates/{self.template.id}/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Template.objects.filter(pk=self.template.id).exists())


class AdminDeploymentTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com', full_name='Admin', password='Str0ngPass!23'
        )
        self.admin.role = User.ADMIN
        self.admin.is_verified = True
        self.admin.save(update_fields=['role', 'is_verified'])

        self.dev = User.objects.create_user(
            email='dev@example.com', full_name='Dev', password='Str0ngPass!23'
        )
        self.deployable = Template.objects.create(
            name='Solo Portfolio', category=Template.PORTFOLIO,
            description='x', source_path='solo-portfolio',
        )
        self.undeployable = Template.objects.create(
            name='Agency One', category=Template.AGENCY, description='x',
        )
        self.project = Project.objects.create(
            developer=self.dev, template=self.deployable, name='Dev Site'
        )
        self.failing_project = Project.objects.create(
            developer=self.dev, template=self.undeployable, name='Broken Site'
        )

    def test_requires_admin(self):
        self.client.force_authenticate(self.dev)
        res = self.client.get('/api/admin/deployments/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_lists_deployments_across_all_developers(self):
        run_deploy(self.project)
        run_deploy(self.failing_project)

        self.client.force_authenticate(self.admin)
        res = self.client.get('/api/admin/deployments/')

        self.assertEqual(len(res.data), 2)
        by_project = {row['project_name']: row for row in res.data}
        self.assertEqual(by_project['Dev Site']['status'], 'SUCCESS')
        self.assertEqual(by_project['Dev Site']['developer_email'], 'dev@example.com')
        self.assertEqual(by_project['Broken Site']['status'], 'FAILED')

    def test_filters_by_status(self):
        run_deploy(self.project)
        run_deploy(self.failing_project)

        self.client.force_authenticate(self.admin)
        res = self.client.get('/api/admin/deployments/', {'status': 'failed'})

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['project_name'], 'Broken Site')

    def test_overview_counts_deployments(self):
        run_deploy(self.project)
        run_deploy(self.failing_project)

        self.client.force_authenticate(self.admin)
        res = self.client.get('/api/admin/overview/')

        self.assertEqual(res.data['total_deployments'], 2)
        self.assertEqual(res.data['failed_deployments'], 1)
