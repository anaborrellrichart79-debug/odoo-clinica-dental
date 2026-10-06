from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

# La clínica cierra a las 20:00 (en minutos desde las 00:00)
HORA_CIERRE = 20 * 60


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
    # La recepción elige el día y una hora libre; la fecha y hora se calcula
    dia = fields.Date(string='Día', required=True)
    hora_id = fields.Many2one(
        'clinica.hora',
        string='Hora',
        required=True,
        ondelete='restrict')
    horas_libres_ids = fields.Many2many(
        'clinica.hora',
        string='Horas libres',
        compute='_compute_horas_libres_ids')
    fecha = fields.Datetime(
        string='Fecha y hora',
        compute='_compute_fecha',
        store=True,
        precompute=True,
        required=True,
        tracking=True)
    tratamiento_id = fields.Many2one(
        'clinica.tratamiento',
        string='Tratamiento',
        required=True,
        ondelete='restrict',
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

    def _a_utc(self, dia, minutos):
        """Día + minutos desde las 00:00 en la hora local -> datetime en UTC.

        Odoo guarda los Datetime en UTC y los muestra en la zona del usuario.
        """
        zona = ZoneInfo(self.env.user.tz or 'Europe/Madrid')
        local = datetime.combine(dia, datetime.min.time()) + timedelta(minutes=minutos)
        return local.replace(tzinfo=zona).astimezone(timezone.utc).replace(tzinfo=None)

    @api.depends('dia', 'hora_id')
    def _compute_fecha(self):
        for cita in self:
            if cita.dia and cita.hora_id:
                cita.fecha = cita._a_utc(cita.dia, cita.hora_id.minutos)
            else:
                cita.fecha = False

    @api.depends('dia', 'duracion')
    def _compute_horas_libres_ids(self):
        horas = self.env['clinica.hora'].search([])
        for cita in self:
            if not cita.dia:
                cita.horas_libres_ids = False
                continue
            # Citas de ese día que ocupan la agenda (sin contar esta misma)
            otras = self.search([
                ('id', '!=', cita._origin.id),
                ('estado', '!=', 'cancelada'),
                ('fecha', '<', cita._a_utc(cita.dia, 24 * 60)),
                ('fecha_fin', '>', cita._a_utc(cita.dia, 0)),
            ])
            libres = self.env['clinica.hora']
            for hora in horas:
                # El tratamiento tiene que acabar antes del cierre
                if hora.minutos + cita.duracion > HORA_CIERRE:
                    continue
                inicio = cita._a_utc(cita.dia, hora.minutos)
                fin = inicio + timedelta(minutes=cita.duracion)
                # Libre si no se solapa con ninguna otra (misma condición que _check_fecha)
                if not any(otra.fecha < fin and otra.fecha_fin > inicio for otra in otras):
                    libres |= hora
            cita.horas_libres_ids = libres

    @api.onchange('dia', 'duracion')
    def _onchange_hora_libre(self):
        # Si al cambiar el día o la duración la hora elegida deja de estar libre, se vacía
        # _origin: en el formulario los registros son "nuevos" (NewId); se comparan los reales
        if self.hora_id and self.hora_id._origin not in self.horas_libres_ids._origin:
            self.hora_id = False

    @api.depends('tratamiento_id')
    def _compute_duracion(self):
        for cita in self:
            cita.duracion = cita.tratamiento_id.duracion

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

    # ------------------------------------------------------------------
    # Botones para cambiar el estado de la cita
    #
    #   borrador ──> confirmada ──> realizada
    #      │              │
    #      └──> cancelada <┘
    #              │
    #              └──> borrador   (volver a abrir una cita cancelada)
    #
    # Cada método se llama desde un botón del formulario (type="object").
    # self puede traer varias citas: hay que recorrerlas con un for.
    # ------------------------------------------------------------------

    def action_confirmar(self):
        for cita in self:
            if cita.estado != 'borrador':
                raise UserError(self.env._("No se puede confirmar una cita que no esté en borrador."))
            else:
                cita.estado = 'confirmada'

    def action_realizar(self):
        # Solo un doctor puede dar una cita por realizada (el botón ya está
        # oculto para recepción, pero la regla de verdad está aquí)
        if not self.env.user.has_group('clinica_pacientes.group_doctor'):
            raise UserError(self.env._("Solo un doctor puede marcar una cita como realizada."))
        for cita in self:
            if cita.estado != 'confirmada':
                raise UserError(self.env._("No se puede realizar una cita que no esté confirmada."))
            else:
                cita.estado = 'realizada'

    def action_cancelar(self):
        for cita in self:
            if cita.estado not in ('borrador', 'confirmada'):
                raise UserError(self.env._("No se puede cancelar una cita que no esté en borrador o confirmada."))
            else:
                cita.estado = 'cancelada'

    def action_borrador(self):
        for cita in self:
            if cita.estado != 'cancelada':
                raise UserError(self.env._("Solo se puede volver a borrador desde una cita cancelada."))
            else:
                cita.estado = 'borrador'
