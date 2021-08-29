# -*- coding: utf-8 -*-
{
    'name': "Mercadopago Órdenes presenciales",

    'summary': """
    Pago mediante QR mercadopago
    """,

    'description': """
        Pago mediante QR mercadopago mercadopago Órdenes presenciales
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
