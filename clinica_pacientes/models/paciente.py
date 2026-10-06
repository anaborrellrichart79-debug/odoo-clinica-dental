from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ClinicaPaciente(models.Model):
    _name = 'clinica.paciente'
    _description = 'Paciente'
    _inherit = ['mail.thread']
    _rec_name = 'nombre'
    _order = 'nombre'

    nombre = fields.Char(string='Nombre', required=True, tracking=True)
    telefono = fields.Char(string='Teléfono', tracking=True)
    fecha_nacimiento = fields.Date(string='Fecha de nacimiento')

    edad = fields.Integer(string='Edad', compute='_compute_edad')

    tratamiento_habitual_id = fields.Many2one(
        'clinica.tratamiento', string='Tratamiento habitual',
        ondelete='restrict', tracking=True)
    notas = fields.Text(string='Notas')
    # Lado inverso de clinica.cita.paciente_id (no crea columna)
    cita_ids = fields.One2many('clinica.cita', 'paciente_id', string='Citas')
    num_citas = fields.Integer(string='Número de citas', compute='_compute_num_citas')

    @api.depends('cita_ids')
    def _compute_num_citas(self):
        for paciente in self:
            paciente.num_citas = len(paciente.cita_ids)

    @api.depends('fecha_nacimiento')
    def _compute_edad(self):
        for paciente in self:
            if paciente.fecha_nacimiento:
                hoy = fields.Date.today()
                paciente.edad = relativedelta(hoy, paciente.fecha_nacimiento).years
            else:
                paciente.edad = 0

    @api.constrains('fecha_nacimiento')
    def _check_fecha_nacimiento(self):
        for paciente in self:
            if paciente.fecha_nacimiento and paciente.fecha_nacimiento > fields.Date.today():
                raise ValidationError(self.env._("La fecha de nacimiento no puede ser futura."))
