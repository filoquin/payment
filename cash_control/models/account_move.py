# -*- coding: utf-8 -*-
from odoo import fields, models

import logging
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):

    _inherit = 'account.move'

    cash_control_session_id = fields.Many2one(
        'cash.control.session',
        string='Session',
        copy=False,
    )

    config_id = fields.Many2one(
        'cash.control.config',
        related='cash_control_session_id.config_id',
        string="Cash Control",
        readonly=False
    )
