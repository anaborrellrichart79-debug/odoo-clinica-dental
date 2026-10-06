# Clínica dental para Odoo 20

Módulo `clinica_pacientes` para **Odoo 20.0 Community**: gestión de pacientes y citas de una clínica dental, con una agenda única que no permite citas solapadas.

## Funcionalidades

- **Pacientes:** datos de contacto, edad calculada, tratamiento habitual, número de citas, notas e historial de cambios (chatter).
- **Tratamientos configurables:** la clínica crea sus tratamientos con su duración (limpieza 30 min, ortodoncia 30 min, prótesis 60 min de inicio).
- **Agenda sin solapes:** al crear una cita se elige el día y un desplegable que **solo muestra las horas libres**, según la duración del tratamiento y la hora de cierre. Las citas canceladas no ocupan hueco. Una restricción vuelve a comprobarlo al guardar.
- **Estados de la cita:** borrador → confirmada → realizada, o cancelada, con botones y barra de estados.
- **Seguridad:** grupos *Recepción* (gestiona pacientes y agenda) y *Doctor* (además borra, configura tratamientos y marca las citas como realizadas).
- **Informe PDF:** ficha del paciente con su historial de citas y el total sin las canceladas.
- **26 tests automáticos** de pacientes, citas y permisos.

## Instalación

```bash
./odoo-bin -d <base_de_datos> --addons-path=addons,<ruta>/custom-addons -i clinica_pacientes
```

Depende de `base` y `mail`. Para el PDF hace falta [wkhtmltopdf](https://github.com/wkhtmltopdf/packaging/releases) 0.12.6.1.

## Tests

```bash
./odoo-bin -d <base_nueva> --addons-path=addons,<ruta>/custom-addons \
    -i clinica_pacientes --test-tags /clinica_pacientes --stop-after-init
```

## Estructura

```text
clinica_pacientes/
├── models/       paciente, cita, tratamiento, hora de la agenda
├── views/        listas, formularios, búsquedas y menús
├── security/     grupos y permisos (formato ir.access.csv de Odoo 20)
├── data/         tratamientos iniciales y horas de la agenda
├── report/       informe PDF «Ficha del paciente»
├── migrations/   migración de datos a la versión 20.0.1.1.0
└── tests/        tests automáticos
```

Los nombres técnicos están en castellano (`nombre`, `paciente_id`, `action_confirmar`), manteniendo los prefijos habituales de Odoo.

---

Ana Borrell Richart · [Portfolio](https://anaborrellrichart79-debug.github.io/portfolio-personal) · [GitHub](https://github.com/anaborrellrichart79-debug)
