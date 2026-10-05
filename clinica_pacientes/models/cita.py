from odoo import fields, models

from .paciente import TRATAMIENTOS


class ClinicaCita(models.Model):
    _name = 'clinica.cita'
    _description = 'Cita'
    _inherit = ['mail.thread']
    _rec_name = 'paciente_id'
    _order = 'fecha desc'

    paciente_id = fields.Many2one(
        'clinica.paciente', string='Paciente',
        required=True, ondelete='restrict', tracking=True)
    fecha = fields.Datetime(string='Fecha y hora', required=True, tracking=True)
    tratamiento = fields.Selection(TRATAMIENTOS, string='Tratamiento', tracking=True)
    # Moneda del importe: por defecto, la de la compañía del usuario
    currency_id = fields.Many2one(
        'res.currency', string='Moneda',
        default=lambda self: self.env.company.currency_id)
    importe = fields.Monetary(string='Importe', tracking=True)
    estado = fields.Selection(
        [
            ('borrador', 'Borrador'),
            ('confirmada', 'Confirmada'),
            ('realizada', 'Realizada'),
            ('cancelada', 'Cancelada'),
        ],
        string='Estado', default='borrador', required=True, tracking=True)
    notas = fields.Text(string='Notas')
