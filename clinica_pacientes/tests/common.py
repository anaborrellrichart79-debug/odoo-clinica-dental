from datetime import date

from odoo.tests import TransactionCase


class ClinicaCommon(TransactionCase):
    """Datos compartidos por todos los tests de la clínica."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Zona horaria fija: los tests no dependen del usuario que los ejecute
        cls.env.user.tz = 'Europe/Madrid'
        cls.limpieza = cls.env.ref('clinica_pacientes.tratamiento_limpieza')
        cls.protesis = cls.env.ref('clinica_pacientes.tratamiento_protesis')
        cls.sofia = cls.env['clinica.paciente'].create({'nombre': 'Sofía'})
        cls.laura = cls.env['clinica.paciente'].create({'nombre': 'Laura'})
        # Un día futuro fijo para que las citas no dependan de la fecha de hoy
        cls.dia = date(2030, 1, 7)

    @classmethod
    def hora(cls, texto):
        """'10:30' -> registro clinica.hora de esa hora."""
        return cls.env.ref('clinica_pacientes.hora_' + texto.replace(':', ''))

    @classmethod
    def crear_cita(cls, paciente, tratamiento, hora, dia=None, env=None):
        env = env or cls.env
        return env['clinica.cita'].create({
            'paciente_id': paciente.id,
            'tratamiento_id': tratamiento.id,
            'dia': dia or cls.dia,
            'hora_id': cls.hora(hora).id,
            'importe': 50,
        })
