# -*- coding: utf-8 -*-
{
    'name': "plus pagos payment",

    'summary': """Pagos con plus pagos""",

    'description': """
        Pagos con plus pagos
    """,

    'author': "filoquin",
    'website': "http://www.hormigag.ar",

    'category': 'apyment',
    'version': '13.0.0.0.1',

    'depends': ['payment'],

    # always loaded
    'data': [
        'data/payment_acquirer_data.xml',
        'views/payment_acquirer.xml',
    ],
}
