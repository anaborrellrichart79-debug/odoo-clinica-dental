from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .paciente import TRATAMIENTOS


class DuracionTratamiento(models.Model):
    _name = 'clinica.duracion.tratamiento'
    _description = 'Duración por tratamiento'
    _rec_name = 'tratamiento'

    tratamiento = fields.Selection(TRATAMIENTOS, string='Tratamiento', required=True)
    minutos = fields.Integer(string='Duración (minutos)', required=True)

    # Una sola fila por tratamiento (restricción en la base de datos)
    _tratamiento_unico = models.Constraint(
        'UNIQUE (tratamiento)',
        'Ya existe una duración para este tratamiento.',
    )

    @api.constrains('minutos')
    def _check_minutos(self):
        for record in self:
            if record.minutos <= 0:
                raise ValidationError(self.env._(
                    "La duración del tratamiento debe ser mayor que 0 minutos."))
