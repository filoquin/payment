# -*- coding: utf-8 -*-
{
    "name": "pos qr base",
    "summary": """
        Gestion de pagos con QR dentro del pos
    """,
    "description": """
        QR pos base 
    """,
    "author": "filoquin",
    "website": "https://www.hormigag.ar",
    "category": "sale",
    "version": "13.0.0.0.1",
    "depends": ["point_of_sale", "payment"],
    "data": [
        "security/ir.model.access.csv",
        "views/point_of_sale.xml",
        "views/payment_method_view.xml",
        "views/pos_payment.xml",
        "views/payment_transaction.xml",
    ],
    "qweb": [
        "static/src/xml/pos.xml",
    ],
}
