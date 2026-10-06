from datetime import timezone
from zoneinfo import ZoneInfo


def migrate(cr, version):
    """Rellena el día y la hora de las citas creadas antes de la versión 20.0.1.1.0.

    Esas citas solo tenían `fecha` (en UTC). Se pasa a la hora de la clínica
    y se busca la hora de la agenda que coincide. Se hace con SQL para que
    Odoo no recalcule `fecha` a partir de campos todavía vacíos.
    """
    zona = ZoneInfo('Europe/Madrid')
    cr.execute("SELECT id, fecha FROM clinica_cita WHERE dia IS NULL")
    for cita_id, fecha in cr.fetchall():
        local = fecha.replace(tzinfo=timezone.utc).astimezone(zona)
        cr.execute("SELECT id FROM clinica_hora WHERE minutos = %s",
                   [local.hour * 60 + local.minute])
        hora = cr.fetchone()
        cr.execute("UPDATE clinica_cita SET dia = %s, hora_id = %s WHERE id = %s",
                   [local.date(), hora and hora[0], cita_id])
