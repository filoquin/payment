{
    "name": "Mercadopago Órdenes presenciales",
    "summary": """
    Pago mediante QR mercadopago
    """,
    "description": """
        Pago mediante QR mercadopago
    """,
    "license": "LGPL-3",
    "author": "filoquin",
    "website": "http://www.hormigag.ar",
    "category": "sale",
    "version": "16.0.1.0.0",
    "depends": ["payment"],
    "data": [
        "security/ir.model.access.csv",
        "data/payment_provider_data.xml",
        "views/payment_provider.xml",
        "views/payment_transaction.xml",
        "wizards/payment_link_wizard.xml",
        "wizards/payment_qr_wizard.xml",
    ],
    "demo": [
        "demo/demo.xml",
    ],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
}
