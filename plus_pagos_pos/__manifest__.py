# -*- coding: utf-8 -*-
{
    "name": "plus pagos pos",
    "summary": """ plus pagos pos""",
    "description": """
        plus pagos pos
    """,
    "author": "filoquin",
    "website": "http://www.hormigag.ar",
    "category": "sale",
    "version": "13.0.0.0.1",
    "depends": ["point_of_sale", "payment", "plus_pagos_payment", "pos_qr_base"],
    # always loaded
    "data": [
        # 'security/ir.model.access.csv',
        "views/pos_config.xml",
    ],
}
