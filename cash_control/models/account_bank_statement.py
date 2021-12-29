# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class account_bank_statement(models.Model):
    _inherit = 'account.bank.statement'

    cash_control_session_id = fields.Many2one(
        'cash.control.session',
        string='Cash Control Session',
        copy=False
    )

    @api.constrains('journal_id', 'balance_start', 'cash_control_session_id')
    def chek_session(self):
        if self.journal_id.type == 'cash' and self.cash_control_session_id:
            if self.balance_start != self.cash_control_session_id.previous_session_id.statement_balance_end:
                raise UserError(_('Las balance end not eq balance start'))


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    payment_statement_id = fields.Many2one(
        'account.payment', string="Payment statement", ondelete='cascade')
