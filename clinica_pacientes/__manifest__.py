{
    'name': 'Clínica Dental - Pacientes',
    'version': '20.0.1.0.0',
    'category': 'Services',
    'summary': 'Gestión de pacientes y citas de una clínica dental',
    'author': 'Ana Borrell Richart',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    # Archivos XML/CSV que se cargan al instalar (el orden importa)
    'data': [
        'security/ir.access.csv',
        'views/paciente_views.xml',
        'views/cita_views.xml',
        'views/duracion_tratamiento_views.xml',
        'views/menus.xml',
        'data/duracion_data.xml',
    ],
    'application': True,
    'installable': True,
}
