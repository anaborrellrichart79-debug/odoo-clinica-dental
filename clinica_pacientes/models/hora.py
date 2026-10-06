from odoo import fields, models


class ClinicaHora(models.Model):
    _name = 'clinica.hora'
    _description = 'Hora de la agenda'
    _rec_name = 'nombre'
    _order = 'minutos'

    nombre = fields.Char(string='Hora', required=True)
    # Minutos desde las 00:00 (09:30 -> 570): sirve para hacer cuentas
    minutos = fields.Integer(string='Minutos', required=True)
