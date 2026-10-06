{
    'name': 'Clínica Dental - Pacientes',
    'version': '20.0.1.1.0',
    'category': 'Services',
    'summary': 'Gestión de pacientes y citas de una clínica dental',
    'author': 'Ana Borrell Richart',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    # Archivos XML/CSV que se cargan al instalar (el orden importa)
    'data': [
        'security/clinica_security.xml',
        'security/ir.access.csv',
        'views/paciente_views.xml',
        'views/cita_views.xml',
        'views/tratamiento_views.xml',
        'views/menus.xml',
        'data/tratamiento_data.xml',
        'data/hora_data.xml',
    ],
    'application': True,
    'installable': True,
}
