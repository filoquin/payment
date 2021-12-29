# -*- coding: utf-8 -*-
from odoo import fields, models, api

import logging
_logger = logging.getLogger(__name__)


class AccountBankStmtCashWizard(models.Model):
    _inherit = 'account.bank.statement.cashbox'

    is_a_template = fields.Boolean(default=False)

    @api.model
    def default_get(self, fields):
        vals = super(AccountBankStmtCashWizard, self).default_get(fields)
        if "is_a_template" in fields and self.env.context.get('default_is_a_template'):
            vals['is_a_template'] = True
        config_id = self.env.context.get('default_pos_id')
        if config_id:
            config = self.env['cash.control.config'].browse(config_id)
            if config.last_session_closing_cashbox.cashbox_lines_ids:
                lines = config.last_session_closing_cashbox.cashbox_lines_ids
            else:
                lines = config.default_cashbox_id.cashbox_lines_ids
            if self.env.context.get('balance', False) == 'start':
                vals['cashbox_lines_ids'] = [[0, 0, {'coin_value': line.coin_value, 'number': line.number, 'subtotal': line.subtotal}] for line in lines]
            else:
                vals['cashbox_lines_ids'] = [[0, 0, {'coin_value': line.coin_value, 'number': 0, 'subtotal': 0.0}] for line in lines]
        return vals

    def _validate_cashbox(self):
        super(AccountBankStmtCashWizard, self)._validate_cashbox()
        session_id = self.env.context.get('pos_session_id')
        if session_id:
            current_session = self.env['cash.control.session'].browse(session_id)
            if current_session.state == 'draft':
                current_session.write({'state': 'opened'})
