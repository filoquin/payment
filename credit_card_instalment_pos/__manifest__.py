# -*- coding: utf-8 -*-
{
    'name': "Implent in pos credit card instalment",

    'summary': "",

    'description': """
    """,
    'author': "Filoquin",
    'website': "http://www.sipecu.com.ar",

    'category': 'pos',
    'version': '13.0.0.1',

    'depends': ['credit_card_instalment', 'point_of_sale'],

    'data': [
        # 'security/ir.model.access.csv',
        'views/pos_payment_method.xml',
        'views/pos_make_payment.xml',
        'views/point_of_sale.xml',
        'views/pos_payment.xml',
    ],
    'qweb': [
        'static/src/xml/card_instalment.xml',
    ],
}
