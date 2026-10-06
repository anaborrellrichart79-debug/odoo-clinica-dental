from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ClinicaTratamiento(models.Model):
    _name = 'clinica.tratamiento'
    _description = 'Tratamiento'
    _rec_name = 'nombre'
    _order = 'nombre'

    nombre = fields.Char(string='Nombre', required=True)
    duracion = fields.Integer(string='Duración (minutos)', required=True, default=30)
    # Archivar en lugar de borrar: un tratamiento con citas no se puede borrar
    active = fields.Boolean(string='Activo', default=True)

    # Un solo tratamiento con cada nombre (restricción en la base de datos)
    _nombre_unico = models.Constraint(
        'UNIQUE (nombre)',
        'Ya existe un tratamiento con este nombre.',
    )

    @api.constrains('duracion')
    def _check_duracion(self):
        for tratamiento in self:
            if tratamiento.duracion <= 0:
                raise ValidationError(self.env._(
                    "La duración del tratamiento debe ser mayor que 0 minutos."))
