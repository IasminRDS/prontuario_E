from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def perfil_requerido(*perfis):
    """Decorador que restringe acesso por perfil de usuário."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.perfil not in perfis and current_user.perfil != 'admin':
                flash('Você não tem permissão para acessar esta área.', 'danger')
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def medico_requerido(f):
    return perfil_requerido('medico', 'admin')(f)

def admin_requerido(f):
    return perfil_requerido('admin')(f)
