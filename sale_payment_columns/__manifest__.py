# -*- coding: utf-8 -*-
{
    'name': "Metodos de pago",

    'summary': """Metodos de pago en el presupuesto""",

    'description': """
        Metodos de pago en el presupuesto
    """,

    'author': "Filoquin",
    'website': "http://www.blancoamor.com",

    'category': 'sale',
    'version': '13.0.0.0.1',

    'depends': ['sale', 'credit_card_instalment_sale', 'website_sale_coupon'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order.xml',
        'views/instalment_template.xml',
    ],
}
