import warnings
from django.apps import AppConfig


# ── Live model patches (for running server) ───────────────────────────────────

def _patch_live_models():
    """Patch live model _meta.db_table so ORM queries use new table names."""
    from django.contrib.auth.models import User, Group, Permission
    from django.contrib.admin.models import LogEntry
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.sessions.models import Session

    User._meta.db_table = 'users'
    User.groups.through._meta.db_table = 'user_roles'
    User.user_permissions.through._meta.db_table = 'user_permissions'
    Group._meta.db_table = 'roles'
    Group.permissions.through._meta.db_table = 'role_permissions'
    Permission._meta.db_table = 'permissions'
    LogEntry._meta.db_table = 'activity_logs'
    ContentType._meta.db_table = 'content_types'
    Session._meta.db_table = 'sessions'


# ── Migration state patches (for manage.py migrate post_migrate) ──────────────

def _patch_state_apps(state_apps):
    """Patch the migration state app registry so post_migrate uses new names."""
    if state_apps is None:
        return
    _patches = {
        ('contenttypes', 'ContentType'): 'content_types',
        ('auth',         'Permission'):  'permissions',
        ('auth',         'Group'):       'roles',
        ('auth',         'User'):        'users',
        ('admin',        'LogEntry'):    'activity_logs',
        ('sessions',     'Session'):     'sessions',
    }
    for (app, model), table in _patches.items():
        try:
            state_apps.get_model(app, model)._meta.db_table = table
        except Exception:
            pass


def _install_emit_patch():
    """
    Replace manage.py migrate's emit_post_migrate_signal with a version
    that first patches the migration state model db_table values so that
    post_migrate receivers (create_permissions, create_contenttypes) query
    the correct (renamed) tables.
    Only patches when the rename has already been applied (users table exists).
    """
    try:
        import django.core.management.commands.migrate as _cmd
        _orig = _cmd.emit_post_migrate_signal

        def _patched(*args, **kwargs):
            # Check if tables have been renamed (users exists → renamed)
            db = kwargs.get('db') or (args[2] if len(args) > 2 else 'default')
            try:
                from django.db import connections
                with connections[db].cursor() as cur:
                    cur.execute("SHOW TABLES LIKE 'users'")
                    if cur.fetchone():
                        _patch_state_apps(kwargs.get('apps'))
            except Exception:
                pass
            return _orig(*args, **kwargs)

        _cmd.emit_post_migrate_signal = _patched
    except Exception:
        pass


# ── post_migrate: rename auth/system tables after first migrate ───────────────

def _rename_tables_on_post_migrate(sender, **kwargs):
    """
    Runs as landsystem's post_migrate (after auth/contenttypes/admin handlers).
    Renames auth_ and django_ tables to clean business names.
    Idempotent — skips any table that has already been renamed.
    """
    from django.db import connection
    renames = [
        ('auth_user',                  'users'),
        ('auth_group',                 'roles'),
        ('auth_permission',            'permissions'),
        ('auth_user_groups',           'user_roles'),
        ('auth_user_user_permissions', 'user_permissions'),
        ('auth_group_permissions',     'role_permissions'),
        ('django_admin_log',           'activity_logs'),
        ('django_content_type',        'content_types'),
        ('django_session',             'sessions'),
    ]
    with connection.cursor() as cursor:
        for old, new in renames:
            cursor.execute('SHOW TABLES LIKE %s', [old])
            if cursor.fetchone():
                cursor.execute(f'RENAME TABLE `{old}` TO `{new}`')

    # Patch live models immediately so current process uses new names
    _patch_live_models()


# ── AppConfig ─────────────────────────────────────────────────────────────────

class LandsystemConfig(AppConfig):
    name = 'landsystem'

    def ready(self):
        from django.db.models.signals import post_migrate

        # Intercept emit_post_migrate_signal so post_migrate uses new table names
        _install_emit_patch()

        # Rename tables after first-time migrate (our handler fires last)
        post_migrate.connect(_rename_tables_on_post_migrate, sender=self)

        # Patch live models on server start (tables already renamed)
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=RuntimeWarning)
            try:
                from django.db import connection
                tables = connection.introspection.table_names()
                if 'users' in tables:
                    _patch_live_models()
            except Exception:
                pass



