from . import controllers
from . import models
from . import wizards

from odoo.addons.payment import setup_provider, reset_payment_provider


def post_init_hook(env):
    setup_provider(env, "mercado_pago_qr")


def uninstall_hook(env):
    reset_payment_provider(env, "mercado_pago_qr")
