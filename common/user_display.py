"""Texto amigável para exibir usuário em auditoria (API / PDF)."""


def usuario_exibicao(user) -> str | None:
    if user is None:
        return None
    nome = (user.get_full_name() or '').strip()
    if nome:
        return nome
    email = (getattr(user, 'email', None) or '').strip()
    if email:
        return email
    return getattr(user, 'username', None) or None
