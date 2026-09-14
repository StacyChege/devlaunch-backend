"""The F3 "build pipeline". Synchronous — there's no per-project container
build, just a template render (see templates.rendering) — but every
Deployment still moves through Queued -> Building -> Success/Failed so the
API and audit trail match the PRD, and it's a natural place to slot in a
real async pipeline later without changing callers.
"""
from templates.rendering import TemplateSourceMissing, render_site

from .models import Deployment, Project


def run_deploy(project):
    """Create and run a Deployment for `project`'s current customisation_data.

    Always returns the Deployment (SUCCESS or FAILED) rather than raising —
    a failed build is a normal, recorded outcome, not an exception.
    """
    deployment = Deployment.objects.create(project=project, status=Deployment.STATUS_QUEUED)

    if not project.template:
        return _fail(deployment, project, 'Project has no template attached.')

    deployment.status = Deployment.STATUS_BUILDING
    deployment.save(update_fields=['status'])

    try:
        html = render_site(project.template, project.name, project.customisation_data)
    except TemplateSourceMissing as exc:
        return _fail(deployment, project, str(exc))
    except Exception as exc:  # pragma: no cover - defensive, unexpected renderer error
        return _fail(deployment, project, f'Unexpected build error: {exc}')

    deployment.status = Deployment.STATUS_SUCCESS
    deployment.html = html
    deployment.build_log = 'Build completed successfully.'
    deployment.save(update_fields=['status', 'html', 'build_log'])

    project.status = Project.STATUS_DEPLOYED
    project.save(update_fields=['status'])
    return deployment


def run_rollback(project):
    """Re-publish the previous successful deployment as a new one.

    Append-only: nothing is mutated or deleted, so history stays intact.
    Raises ValueError (caller turns this into a 400) when there's nothing
    to roll back to.
    """
    successes = project.deployments.filter(status=Deployment.STATUS_SUCCESS)
    current = successes.first()
    if not current:
        raise ValueError('No successful deployment to roll back from.')

    previous = successes.exclude(pk=current.pk).first()
    if not previous:
        raise ValueError('No earlier successful deployment to roll back to.')

    rollback = Deployment.objects.create(
        project=project,
        status=Deployment.STATUS_SUCCESS,
        html=previous.html,
        build_log=(
            f'Rolled back to deployment #{previous.pk} '
            f'({previous.created_at:%Y-%m-%d %H:%M}).'
        ),
        is_rollback=True,
    )
    project.status = Project.STATUS_DEPLOYED
    project.save(update_fields=['status'])
    return rollback


def _fail(deployment, project, message):
    deployment.status = Deployment.STATUS_FAILED
    deployment.build_log = message
    deployment.save(update_fields=['status', 'build_log'])
    project.status = Project.STATUS_FAILED
    project.save(update_fields=['status'])
    return deployment
