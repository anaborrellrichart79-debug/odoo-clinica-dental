from odoo import fields, models

# Opciones de tratamiento, compartidas con clinica.cita
TRATAMIENTOS = [
    ('limpieza', 'Limpieza'),
    ('ortodoncia', 'Ortodoncia'),
    ('protesis', 'Prótesis'),
]


class ClinicaPaciente(models.Model):
    _name = 'clinica.paciente'
    _description = 'Paciente'
    _inherit = ['mail.thread']
    _rec_name = 'nombre'
    _order = 'nombre'

    nombre = fields.Char(string='Nombre', required=True, tracking=True)
    telefono = fields.Char(string='Teléfono', tracking=True)
    fecha_nacimiento = fields.Date(string='Fecha de nacimiento')
    tratamiento_habitual = fields.Selection(
        TRATAMIENTOS, string='Tratamiento habitual', tracking=True)
    notas = fields.Text(string='Notas')
    # Lado inverso de clinica.cita.paciente_id (no crea columna)
    cita_ids = fields.One2many('clinica.cita', 'paciente_id', string='Citas')
