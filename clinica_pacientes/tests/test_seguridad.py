from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user, tagged

from .common import ClinicaCommon


@tagged('post_install', '-at_install')
class TestSeguridad(ClinicaCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.recepcion = new_test_user(cls.env, login='recepcion', tz='Europe/Madrid',
                                      groups='clinica_pacientes.group_recepcion')
        cls.doctor = new_test_user(cls.env, login='doctor', tz='Europe/Madrid',
                                   groups='clinica_pacientes.group_doctor')
        cls.interno = new_test_user(cls.env, login='interno', groups='base.group_user')

    def test_doctor_implica_recepcion(self):
        self.assertTrue(self.doctor.has_group('clinica_pacientes.group_recepcion'))
        self.assertFalse(self.recepcion.has_group('clinica_pacientes.group_doctor'))

    def test_recepcion(self):
        env = self.env(user=self.recepcion)
        paciente = env['clinica.paciente'].create({'nombre': 'Nuevo'})
        cita = self.crear_cita(paciente, self.limpieza, '10:00', env=env)
        cita.action_confirmar()
        self.assertTrue(env['clinica.tratamiento'].search([]))
        with self.assertRaises(AccessError):
            paciente.unlink()
        with self.assertRaises(AccessError):
            env['clinica.tratamiento'].create({'nombre': 'Implantes', 'duracion': 90})
        with self.assertRaises(UserError):
            cita.action_realizar()

    def test_doctor(self):
        env = self.env(user=self.doctor)
        paciente = env['clinica.paciente'].create({'nombre': 'Nuevo'})
        cita = self.crear_cita(paciente, self.limpieza, '10:00', env=env)
        cita.action_confirmar()
        cita.action_realizar()
        self.assertEqual(cita.estado, 'realizada')
        env['clinica.tratamiento'].create({'nombre': 'Implantes', 'duracion': 90})
        env['clinica.paciente'].create({'nombre': 'Borrar'}).unlink()

    def test_usuario_sin_grupo(self):
        env = self.env(user=self.interno)
        with self.assertRaises(AccessError):
            env['clinica.paciente'].search([])

    def test_menus(self):
        raiz = self.env.ref('clinica_pacientes.clinica_menu_root')
        configuracion = self.env.ref('clinica_pacientes.menu_clinica_configuracion')
        visibles = self.env['ir.ui.menu'].with_user(self.recepcion)._visible_menu_ids()
        self.assertIn(raiz.id, visibles)
        self.assertNotIn(configuracion.id, visibles)
        visibles = self.env['ir.ui.menu'].with_user(self.doctor)._visible_menu_ids()
        self.assertIn(configuracion.id, visibles)
        visibles = self.env['ir.ui.menu'].with_user(self.interno)._visible_menu_ids()
        self.assertNotIn(raiz.id, visibles)
