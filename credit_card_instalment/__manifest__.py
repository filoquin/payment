# -*- coding: utf-8 -*-
{
    'name': "credit card instalment",

    'summary': "Add concept of credit card instalment",

    'description': """
        Base module for compute instalment and fee on creditcard sales method.
    """,

    'author': "ctmil, Filoquin",
    'website': "http://sipecu.com.ar",
    'category': 'account',
    'version': '13.0.0.1',
    'depends': ['account'],
    'data': [
        'data/product.xml',

        'security/ir.model.access.csv',
        'views/account_card.xml',

    ],
}
