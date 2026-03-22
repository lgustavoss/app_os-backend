import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Cria um usuário administrador padrão se ainda não existir."

    def handle(self, *args, **options):
        User = get_user_model()

        password = os.getenv("ADMIN_PASSWORD", "admin123")
        email = (os.getenv("ADMIN_EMAIL", "admin@example.com") or "").strip().lower()
        if not email:
            email = "admin@example.com"

        if User.objects.filter(email__iexact=email).exists():
            self.stdout.write(
                self.style.WARNING(f"Já existe usuário com e-mail '{email}', nada a fazer.")
            )
            return

        User.objects.create_superuser(
            username=email,
            email=email,
            password=password,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Admin criado: e-mail='{email}' (login com este e-mail), senha definida em ADMIN_PASSWORD"
            )
        )

