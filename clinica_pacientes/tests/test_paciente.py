from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import ClinicaCommon


@tagged('post_install', '-at_install')
class TestPaciente(ClinicaCommon):

    def test_edad(self):
        hoy = fields.Date.today()
        # Cumple 30 años hoy
        self.sofia.fecha_nacimiento = hoy - relativedelta(years=30)
        self.assertEqual(self.sofia.edad, 30)
        # Cumple 30 mañana: todavía tiene 29
        self.sofia.fecha_nacimiento = hoy - relativedelta(years=30) + relativedelta(days=1)
        self.assertEqual(self.sofia.edad, 29)

    def test_edad_sin_fecha(self):
        self.assertEqual(self.laura.edad, 0)

    def test_fecha_nacimiento_futura(self):
        manana = fields.Date.today() + relativedelta(days=1)
        with self.assertRaises(ValidationError):
            self.sofia.fecha_nacimiento = manana
        # Nacer hoy sí está permitido
        self.sofia.fecha_nacimiento = fields.Date.today()

    def test_num_citas(self):
        self.assertEqual(self.sofia.num_citas, 0)
        self.crear_cita(self.sofia, self.limpieza, '09:00')
        self.crear_cita(self.sofia, self.limpieza, '11:00')
        self.assertEqual(self.sofia.num_citas, 2)

    def test_informe_ficha(self):
        self.sofia.notas = 'Alergia a la penicilina'
        self.crear_cita(self.sofia, self.protesis, '10:00')
        cancelada = self.crear_cita(self.sofia, self.limpieza, '12:00')
        cancelada.action_cancelar()
        # Se prueba el HTML: el PDF necesita wkhtmltopdf instalado
        html, _tipo = self.env['ir.actions.report']._render_qweb_html(
            'clinica_pacientes.clinica_paciente_report', self.sofia.ids)
        html = html.decode()
        self.assertIn('Sofía', html)
        self.assertIn('Alergia a la penicilina', html)
        self.assertIn('Prótesis', html)
        # El total (50) no incluye la cita cancelada (50 + 50 = 100)
        self.assertRegex(html, r'Total \(sin canceladas\)[\s\S]*?50[.,]00')
        self.assertNotRegex(html, r'Total \(sin canceladas\)[\s\S]*?100[.,]00')
