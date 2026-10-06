from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .paciente import TRATAMIENTOS


class ClinicaCita(models.Model):
    _name = 'clinica.cita'
    _description = 'Cita'
    _inherit = ['mail.thread']
    _rec_name = 'paciente_id'
    _order = 'fecha desc'

    paciente_id = fields.Many2one(
        'clinica.paciente',
        string='Paciente',
        required=True,
        ondelete='restrict',
        tracking=True)
    fecha = fields.Datetime(
        string='Fecha y hora',
        required=True,
        tracking=True)
    tratamiento = fields.Selection(
        TRATAMIENTOS,
        string='Tratamiento',
        required=True,
        tracking=True)
    # Moneda del importe: por defecto, la de la compañía del usuario
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id)
    importe = fields.Monetary(
        string='Importe',
        currency_field='currency_id',
        required=True,
        tracking=True
    )
    estado = fields.Selection(
        [
            ('borrador', 'Borrador'),
            ('confirmada', 'Confirmada'),
            ('realizada', 'Realizada'),
            ('cancelada', 'Cancelada'),
        ],
        string='Estado', default='borrador', required=True, tracking=True)
    notas = fields.Text(string='Notas')

    # Se propone según el tratamiento, pero se puede cambiar en cada cita.
    # precompute: se calcula antes del INSERT (si no, choca con required)
    duracion = fields.Integer(
        string='Duración (minutos)',
        compute='_compute_duracion',
        store=True,
        precompute=True,
        readonly=False,
        required=True,
    )
    fecha_fin = fields.Datetime(
        string='Fecha y hora fin',
        compute='_compute_fecha_fin',
        store=True,
    )

    @api.depends('tratamiento')
    def _compute_duracion(self):
        for cita in self:
            duracion = self.env['clinica.duracion.tratamiento'].search(
                [('tratamiento', '=', cita.tratamiento)], limit=1)
            if duracion:
                cita.duracion = duracion.minutos
            else:
                cita.duracion = 15

    @api.depends('fecha', 'duracion')
    def _compute_fecha_fin(self):
        for cita in self:
            if cita.fecha and cita.duracion:
                cita.fecha_fin = cita.fecha + timedelta(minutes=cita.duracion)
            else:
                cita.fecha_fin = cita.fecha

    @api.constrains('fecha', 'fecha_fin', 'estado')
    def _check_fecha(self):
        for cita in self:
            # Una cita cancelada no ocupa la agenda
            if cita.estado == 'cancelada':
                continue
            # Se solapan si una empieza antes de que acabe la otra
            # y acaba después de que empiece la otra
            citas_conflictivas = self.search([
                ('id', '!=', cita.id),
                ('estado', '!=', 'cancelada'),
                ('fecha', '<', cita.fecha_fin),
                ('fecha_fin', '>', cita.fecha),
            ], limit=1)
            if citas_conflictivas:
                raise ValidationError(self.env._(
                    "La cita se solapa con la cita de %(paciente)s.",
                    paciente=citas_conflictivas.paciente_id.nombre,
                ))
