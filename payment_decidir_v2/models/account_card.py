# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)


DECIDIR_METHODS = [('1', 'Visa'),
                   ('8', 'Diners Club'),
                   ('23', 'Tarjeta Shopping'),
                   ('24', 'Tarjeta Naranja'),
                   ('25', 'PagoFacil'),
                   ('26', 'RapiPago'),
                   ('29', 'Italcred'),
                   ('30', 'ArgenCard'),
                   ('34', 'CoopePlus'),
                   ('37', 'Nexo'),
                   ('38', 'Credimás'),
                   ('39', 'Tarjeta Nevada'),
                   ('42', 'Nativa'),
                   ('43', 'Tarjeta Cencosud'),
                   ('44', 'Tarjeta Carrefour / Cetelem'),
                   ('45', 'Tarjeta PymeNacion'),
                   ('48', 'Caja de Pagos'),
                   ('50', 'BBPS'),
                   ('51', 'Cobro Express'),
                   ('52', 'Qida'),
                   ('54', 'Grupar'),
                   ('55', 'Patagonia 365'),
                   ('56', 'Tarjeta Club Día'),
                   ('59', 'Tuya'),
                   ('60', 'Distribution'),
                   ('61', 'Tarjeta La Anónima'),
                   ('62', 'CrediGuia'),
                   ('63', 'Cabal Prisma'),
                   ('64', 'Tarjeta SOL'),
                   ('65', 'American Express'),
                   ('103', 'Favacard'),
                   ('104', 'MasterCard Prisma'),
                   ('109', 'Nativa Prisma'),
                   ('111', 'American Express Prisma'),
                   ('31', 'Visa Débito'),
                   ('105', 'MasterCard Debit Prisma'),
                   ('106', 'Maestro Prisma'),
                   ('108', 'Cabal Débito Prisma')
                   ]


class AccountCard(models.Model):

    _inherit = 'account.card'

    decidir_method = fields.Selection(
        DECIDIR_METHODS,
        string='Decidir',
    )

