# -*- coding: utf-8 -*-
{
    'name': "Mercado Pago QR payment",

    'summary': """
    Pago mediante QR mercado pago
    """,

    'description': """
        Pago mediante QR mercado pago
    """,

    'author': "filoquin",
    'website': "http://www.hormigag.ar",

    'category': 'sale',
    'version': '13.0.0.0.1',

    'depends': ['payment'],

    'data': [
        # 'security/ir.model.access.csv',
        'views/payment_acquirer.xml',
        'data/payment_acquirer_data.xml',
        
    ],
}
