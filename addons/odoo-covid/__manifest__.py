# __manifest__.py
{
    'name': "covid-italy-regions",
    'summary': "Import and show SARS-CoV-2 data per Italian region",
    'version': '1.0',
    'author': 'Marco Dondo',
    'category': 'Health',
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/covid_data_views.xml',
    ],
}