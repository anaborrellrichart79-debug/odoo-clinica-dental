from datetime import timedelta

from psycopg2 import IntegrityError

from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged
from odoo.tools import mute_logger

from .common import ClinicaCommon


@tagged('post_install', '-at_install')
class TestCita(ClinicaCommon):

    # --- Tratamientos ---------------------------------------------------

    @mute_logger('odoo.sql_db')  # PostgreSQL registra la consulta rechazada
    def test_tratamiento_nombre_unico(self):
        # La restricción UNIQUE está en PostgreSQL: salta al escribir en la base
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self.env['clinica.tratamiento'].create({'nombre': 'Limpieza', 'duracion': 20})
            self.env.flush_all()

    def test_tratamiento_duracion_positiva(self):
        with self.assertRaises(ValidationError):
            self.env['clinica.tratamiento'].create({'nombre': 'Blanqueamiento', 'duracion': 0})

    # --- Duración y hora de fin -----------------------------------------

    def test_duracion_y_fecha_fin(self):
        cita = self.crear_cita(self.sofia, self.protesis, '10:00')
        self.assertEqual(cita.duracion, 60)
        self.assertEqual(cita.fecha_fin - cita.fecha, timedelta(minutes=60))

    def test_fecha_en_hora_local(self):
        # 10:00 en Madrid (invierno, UTC+1) se guarda como 09:00 UTC
        cita = self.crear_cita(self.sofia, self.limpieza, '10:00')
        self.assertEqual(cita.fecha.hour, 9)

    def test_duracion_editable(self):
        cita = self.crear_cita(self.sofia, self.protesis, '10:00')
        cita.duracion = 45
        self.assertEqual(cita.fecha_fin - cita.fecha, timedelta(minutes=45))

    def test_cambiar_tratamiento_no_mueve_citas(self):
        cita = self.crear_cita(self.sofia, self.limpieza, '10:00')
        self.limpieza.duracion = 45
        self.assertEqual(cita.duracion, 30)

    # --- Solapes ----------------------------------------------------------

    def test_solape_bloqueado(self):
        self.crear_cita(self.sofia, self.protesis, '10:00')       # 10:00-11:00
        with self.assertRaises(ValidationError):
            self.crear_cita(self.laura, self.limpieza, '10:30')

    def test_cita_justo_al_acabar_otra(self):
        self.crear_cita(self.sofia, self.protesis, '10:00')       # 10:00-11:00
        self.crear_cita(self.laura, self.limpieza, '11:00')       # no se solapa

    def test_cancelada_no_bloquea(self):
        cita = self.crear_cita(self.sofia, self.protesis, '10:00')
        cita.action_cancelar()
        self.crear_cita(self.laura, self.limpieza, '10:30')

    def test_reabrir_con_hora_ocupada(self):
        cita = self.crear_cita(self.sofia, self.protesis, '10:00')
        cita.action_cancelar()
        self.crear_cita(self.laura, self.limpieza, '10:30')
        with self.assertRaises(ValidationError):
            cita.action_borrador()

    # --- Horas libres en el formulario -----------------------------------

    def test_horas_libres(self):
        self.crear_cita(self.sofia, self.protesis, '10:00')       # 10:00-11:00
        form = Form(self.env['clinica.cita'])
        form.paciente_id = self.laura
        form.tratamiento_id = self.limpieza                       # 30 min
        form.dia = self.dia
        libres = [hora.nombre for hora in form.horas_libres_ids]
        self.assertIn('09:30', libres)
        self.assertNotIn('10:00', libres)
        self.assertNotIn('10:30', libres)
        self.assertIn('11:00', libres)
        # Con prótesis (60 min) tampoco cabe a las 09:30 ni a las 19:30 (cierre a las 20:00)
        form.tratamiento_id = self.protesis
        libres = [hora.nombre for hora in form.horas_libres_ids]
        self.assertNotIn('09:30', libres)
        self.assertNotIn('19:30', libres)
        self.assertIn('19:00', libres)

    def test_hora_se_vacia_si_deja_de_estar_libre(self):
        self.crear_cita(self.sofia, self.protesis, '10:00')
        form = Form(self.env['clinica.cita'])
        form.paciente_id = self.laura
        form.tratamiento_id = self.limpieza
        form.dia = self.dia
        form.hora_id = self.hora('09:30')
        form.tratamiento_id = self.protesis                       # 09:30-10:30: choca
        self.assertFalse(form.hora_id)

    # --- Estados ----------------------------------------------------------

    def test_flujo_de_estados(self):
        cita = self.crear_cita(self.sofia, self.limpieza, '10:00')
        self.assertEqual(cita.estado, 'borrador')
        cita.action_confirmar()
        self.assertEqual(cita.estado, 'confirmada')
        cita.action_realizar()
        self.assertEqual(cita.estado, 'realizada')

    def test_transiciones_no_permitidas(self):
        cita = self.crear_cita(self.sofia, self.limpieza, '10:00')
        with self.assertRaises(UserError):
            cita.action_realizar()            # desde borrador
        with self.assertRaises(UserError):
            cita.action_borrador()            # no está cancelada
        cita.action_confirmar()
        cita.action_realizar()
        with self.assertRaises(UserError):
            cita.action_cancelar()            # ya realizada
        with self.assertRaises(UserError):
            cita.action_confirmar()
