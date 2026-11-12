
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = "Crea los grupos de usuarios del ERP."

    def handle(self, *args, **options):
        nombres_grupos = [
            "Gerente",
            "Vendedor",
            "Almacén",
        ]

        for nombre in nombres_grupos:
            grupo, creado = Group.objects.get_or_create(name=nombre)

            if creado:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Grupo '{nombre}' creado correctamente."
                    )
                )
            else:
                self.stdout.write(
                    f"El grupo '{nombre}' ya existe."
                )

        self.stdout.write(
            self.style.SUCCESS("Proceso terminado.")
        )
