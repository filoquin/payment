# -*- coding: utf-8 -*-
{
    'name': "mercadopago QR POS",

    'summary': """
            Implementa el QR de mercado pago en el pos
        """,

    'description': """
        Implementa el QR de mercado pago en el pos
    """,

    'author': "filoquin",
    'website': "http://www.hormigag.ar",

    'category': 'sale',
    'version': '13.0.0.0.1',

    'depends': ['point_of_sale', 'payment', 'mercadopago_qr_paymemnt', 'pos_qr_base'],

    'data': [
        #'data/pos_payment_method.xml',
        'views/pos_config.xml',
    ],
}