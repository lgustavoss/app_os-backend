"""
Validadores de senha do sistema:
- apenas comprimento mínimo;
- letras, números e símbolos são permitidos; não exige combinação de tipos.
"""

from django.core.exceptions import ValidationError

# Mínimo de caracteres (ajuste único aqui se precisar)
SENHA_MIN_LENGTH = 6


class SenhaSistemaPasswordValidator:
    """
    Exige somente tamanho mínimo. Qualquer caractere imprimível é aceito
    (letras, números, símbolos), sem obrigar maiúscula, dígito ou símbolo.
    """

    def validate(self, password, user=None):
        if len(password) < SENHA_MIN_LENGTH:
            raise ValidationError(
                f'A senha deve ter pelo menos {SENHA_MIN_LENGTH} caracteres.',
                code='password_too_short',
            )

    def get_help_text(self):
        return (
            f'Use pelo menos {SENHA_MIN_LENGTH} caracteres. '
            'Você pode usar letras, números e símbolos; não é obrigatório incluir todos os tipos.'
        )
