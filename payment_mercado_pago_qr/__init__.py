from . import controllers
from . import models
from . import wizards

from odoo.addons.payment import setup_provider, reset_payment_provider


def post_init_hook(cr, registry):
    setup_provider(cr, registry, "mercado_pago_qr")


def uninstall_hook(cr, registry):
    reset_payment_provider(cr, registry, "mercado_pago_qr")
