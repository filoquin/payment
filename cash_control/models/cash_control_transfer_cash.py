# -*- coding: utf-8 -*-
from odoo import fields, models, api
import datetime
import pytz

import logging
_logger = logging.getLogger(__name__)

from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError


class CashControlTransferCash(models.Model):
    _name = 'cash.control.transfer.cash'
    _description = 'transfer Cash'

    state = fields.Selection(
        [('draft', 'draft'), ('transfer', 'transfer'), ('receipt', 'receipt')],
        string='State',
        default='draft',
        required=True,
    )
    name = fields.Char(
        string='Ref',
        required=True,
    )
    orig_journal_id = fields.Many2one(
        'account.journal',
        string='Origin journal',
        domain=[('type', '=', 'cash'), ],
        required=True,
    )

    dest_cash_control_id = fields.Many2one(
        'cash.control.config',
        string='Dest journal',
        domain=[('session_state', '=', 'opened'), ],
        required=True,
    )

    dest_journal_id = fields.Many2one(
        'account.journal',
        string='Dest journal',
        domain=[('type', '=', 'cash'), ],
        required=False,
    )

    orig_statement_line_id = fields.Many2one(
        'account.bank.statement.line',
        string='Origin statement line',
    )

    dest_statement_line_id = fields.Many2one(
        'account.bank.statement.line',
        string='Dest statement line',
    )

    amount = fields.Float(
        string='amount',
        required=True,
        digits=dp.get_precision('adela dp')

    )

    date = fields.Datetime(
        string='Date',
        default=fields.Date.today()
    )

    def action_transfer(self):
        self.ensure_one()
        close_orig = False
        orig_st = self.env['account.bank.statement'].search(
            [('journal_id', '=', self.orig_journal_id.id), ('state', '=', 'open')],
            limit=1,
            order='id desc' 
        )

        if len(orig_st) == 0:
            orig_st = self.env['account.bank.statement'].with_context(
                {'journal_id': self.orig_journal_id.id}
            ).create({
                'user_id': self.env.user.id,
            })

            close_orig = True

        out_values = {
            'date': fields.Date.today(),
            'statement_id': orig_st.id,
            'journal_id': self.orig_journal_id.id,
            'amount': -self.amount or 0.0,
            'account_id': self.orig_journal_id.default_credit_account_id.id,
            #'account_id': self.orig_journal_id.company_id.transfer_account_id.id,
            'ref': 'tc-%s' % (self.id),
            'name': self.name,
            'transaction_type': 'TRANSFER_OUT',
        }

        statement_line = self.env[
            'account.bank.statement.line'].create(out_values)
        #orig_st.write({'line_ids': [(0, False, out_values)]})

        if close_orig:
            orig_st.balance_end_real = orig_st.balance_end
            orig_st.button_confirm_bank()

        self.orig_statement_line_id = statement_line.id
        self.state = 'transfer'

    """
    def add_account_move(self):
        lines = [(0, 0, {
            'name': self.orig_statement_line_id.name,
            'credit': self.orig_statement_line_id.amount,
            'account_id': 4,
            'statement_line_id': self.orig_statement_line_id.id,
            'statement_id': self.orig_statement_line_id.statement_id.id,
        })]
        move = self.env['account.move'].create({
            'name': '/',
            'partner_id': self.partner_id.id,
            'company_id': self.env.user.company_id.id,
            'journal_id': SALES_JOURNAL,
            'ref': self.name,
            'date': fields.Date.today(),
            'line_ids': lines
        })
        move.post()
    """
    def action_receipt(self):
        self.ensure_one()
        dest_st = self.dest_cash_control_id.current_session_id.statement_id
        self.dest_cash_control_id.transfer_pendientes = False
        if len(dest_st) == 0:
            raise ValidationError('La caja de destino esta cerrada')

        in_values = {
            'date': fields.Date.today(),
            'statement_id': dest_st.id,
            'journal_id': dest_st.journal_id.id,
            'amount': self.amount or 0.0,
            'account_id': dest_st.journal_id.company_id.transfer_account_id.id,
            'ref': 'tc-%s' % (self.id),
            'name': self.name,
            'transaction_type': 'TRANSFER_IN'
        }

        #dest_st.write({'line_ids': [(0, False, in_values)]})
        statement_line = self.env[
            'account.bank.statement.line'].create(in_values)

        self.dest_statement_line_id = statement_line.id
        self.state = 'receipt'
