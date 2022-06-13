# -*- coding: utf-8 -*-
{
    "name": "payment decidir",
    "summary": """
        Metodo de pago Decidir""",
    "description": """
      Metodo de pago Decidir
    """,
    "author": "filoquin",
    "website": "http://www.blancoamor.com",
    "category": "sale",
    "version": "13.0.0.0.1",
    "depends": ["payment", "credit_card_instalment", "sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/payment_acquirer.xml",
        "views/account_card.xml",
        "views/decidir_v2_form.xml",
        "views/payment_transaction.xml",
        "views/templates.xml",
        "views/parcial_refund.xml",
        "data/payment_acquirer_data.xml",
    ],
}
