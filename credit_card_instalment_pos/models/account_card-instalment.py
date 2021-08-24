# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)


class AccountCardInstalment(models.Model):
    _inherit = 'account.card.instalment'

    pos_enabled = fields.Boolean(
        string='POS enabled',
    )

