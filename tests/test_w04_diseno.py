
from pathlib import Path

from django.conf import settings
from django.test import TestCase

BASE_DIR = Path(settings.BASE_DIR)


class DocumentosDisenioTest(TestCase):

    def test_docs_diagrama_er_existe(self):
        self.assertTrue(
            (BASE_DIR / "docs" / "diagramas" / "diagrama_er.md").exists()
        )

    def test_diagrama_er_contiene_mermaid(self):
        path = BASE_DIR / "docs" / "diagramas" / "diagrama_er.md"
        self.assertTrue(path.exists())

        content = path.read_text(encoding="utf-8")
        self.assertIn("mermaid", content.lower())

    def test_diagrama_er_contiene_entidades_clave(self):
        path = BASE_DIR / "docs" / "diagramas" / "diagrama_er.md"
        self.assertTrue(path.exists())

        content = path.read_text(encoding="utf-8").upper()

        for entidad in [
            "CLIENTE",
            "PRODUCTO",
            "VENTA",
            "PROVEEDOR",
            "CATEGORIA",
            "DETALLE_VENTA",
            "PEDIDO",
            "CONFIGURACION_ERP",
        ]:
            self.assertIn(entidad, content)

    def test_entidades_atributos_existe(self):
        self.assertTrue(
            (BASE_DIR / "docs" / "entidades_atributos.md").exists()
        )

    def test_decisiones_diseno_existe(self):
        self.assertTrue(
            (BASE_DIR / "docs" / "decisiones_diseno.md").exists()
        )

    def test_decisiones_diseno_tiene_contenido(self):
        path = BASE_DIR / "docs" / "decisiones_diseno.md"
        self.assertTrue(path.exists())

        content = path.read_text(encoding="utf-8")
        decisiones = [
            linea for linea in content.splitlines()
            if linea.startswith("### D-")
        ]

        self.assertGreaterEqual(len(decisiones), 5)

    def test_sprint1_planning_existe(self):
        self.assertTrue(
            (BASE_DIR / "sprint1_planning.md").exists()
        )

    def test_sprint1_planning_tiene_sprint_goal(self):
        path = BASE_DIR / "sprint1_planning.md"
        self.assertTrue(path.exists())

        content = path.read_text(encoding="utf-8")
        self.assertIn("Sprint Goal", content)
