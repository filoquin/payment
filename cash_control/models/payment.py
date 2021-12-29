# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError

import logging
_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    cash_control_session_id = fields.Many2one(
        'cash.control.session',
        string='Session',
        copy=False
    )
    config_id = fields.Many2one(
        'cash.control.config',
        related='cash_control_session_id.config_id',
        string="Cash Control",
        readonly=False
    )
    statement_ids = fields.One2many(
        'account.bank.statement.line',
        'payment_statement_id',
        string='Payments',
        readonly=True
    )

    def _prepare_bank_statement_line_payment_values(self, data):
        """Create a new payment for the order"""
        args = {
            'amount': data['amount'],
            'date': data.get('payment_date', fields.Date.context_today(self)),
            'name': self.name or '' + ': ' + (data.get('payment_name', '') or ''),
            'partner_id': self.env["res.partner"]._find_accounting_partner(self.partner_id).id or False,
        }

        journal_id = data.get('journal', False)
        statement_id = data.get('statement_id', False)
        assert journal_id or statement_id, "No statement_id or journal_id passed to the method!"

        journal = self.env['account.journal'].browse(journal_id)
        # use the company of the journal and not of the current user
        company_cxt = dict(self.env.context, force_company=journal.company_id.id)
        account_def = self.env['ir.property'].with_context(company_cxt).get('property_account_receivable_id', 'res.partner')
        args['account_id'] = (self.partner_id.property_account_receivable_id.id) or (account_def and account_def.id) or False

        if not args['account_id']:
            if not args['partner_id']:
                msg = _('There is no receivable account defined to make payment.')
            else:
                msg = _('There is no receivable account defined to make payment for the partner: "%s" (id:%d).') % (
                    self.partner_id.name, self.partner_id.id,)
            raise UserError(msg)

        context = dict(self.env.context)
        context.pop('pos_session_id', False)
        for statement in self.cash_control_session_id.statement_ids:
            if int(statement.id) == statement_id:
                journal_id = statement.journal_id.id
                break
            elif statement.journal_id.id == journal_id:
                statement_id = statement.id
                break
        if not statement_id:
            raise UserError(_('You have to open at least one cashbox.'))

        args.update({
            'statement_id': statement_id,
            'payment_statement_id': self.id,
            'journal_id': journal_id,
            'ref': self.cash_control_session_id.name,
        })

        return args

    def add_payment(self, data):
        """Create a new payment for the order"""
        self.ensure_one()

        args = self._prepare_bank_statement_line_payment_values(data)
        context = dict(self.env.context)
        context.pop('pos_session_id', False)
        self.env['account.bank.statement.line'].with_context(context).create(args)
        self.amount_paid = sum(payment.amount for payment in self.statement_ids)
        return args.get('statement_id', False)

    def post(self):
        # busco un session activo
        # si no hay -> warning
        # session = self.env['cash.control.session'].search([
        #     ('user_ids', 'in', self.env.uid),
        #     ('state', '=', 'opened')
        # ])
        for rec in self:
            if not rec.cash_control_session_id:
                session = self.env['cash.control.session'].search([
                    ('user_ids', 'in', self.env.uid),
                    ('state', '=', 'opened')
                ])
                if not session:
                    raise ValidationError(_("There is not open cash session for de the current user. Please open a cash session"))
                if not rec.sale_order_id.cash_control_session_id:
                    rec.sale_order_id.cash_control_session_id = session.id
                rec.cash_control_session_id = session.id
            if rec.cash_control_session_id.state not in ['opened']:
                raise ValidationError(_("The payment session was closed. Please create another payment"))
            if rec.journal_id.type == 'cash':

                bs = self.env['account.bank.statement'].search([
                    ('cash_control_session_id', '=', rec.cash_control_session_id.id),
                    ('journal_id', '=', rec.journal_id.id)
                ])
                if not bs:
                    raise UserError(_('There is not session statement for journal %s.') % rec.journal_id.name)
                data = {
                    'amount': rec.amount if rec.payment_type_copy == 'inbound' else rec.amount * -1,
                    'payment_date': fields.Date.context_today(self),
                    'payment_name': 'Payment %s/%s'%(
                        rec.sale_order_id.name,
                        rec.cash_control_session_id.name
                    ),
                    'journal': rec.journal_id.id,
                    'statement_id': bs,
                }
                rec.add_payment(data)
        return super(AccountPayment, self).post()

