from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    account_card_ids = fields.Many2many(
        'account.card',
        string='Cards',
        related='journal_id.account_card_ids'
    )
    card_id = fields.Many2one(
        'account.card',
        string='Card'
    )

    instalment_id = fields.Many2one(
        'account.card.instalment',
        string='Instalment plan'
    )
    
    instalment = fields.Integer(
        string='instalment plan',
        related="instalment_id.instalment"
    )

    card_type = fields.Selection(
        [('credit', 'credit'), ('debit', 'debit')],
        related="card_id.card_type"
    )

    magnet_bar = fields.Char(
        'magnet bar'
    )
    card_number = fields.Char(
        'Card number'
    )
    tiket_number = fields.Char(
        'Tiket number'
    )
    lot_number = fields.Char(
        'Lot number'
    )
    fee = fields.Float(
        string='Fee',
        default=0,
        compute='change_instalment_id',
        store=True,
    )
    total_amount = fields.Float(
        string='total amount',
        default=0,
        compute='change_instalment_id',
        store=True,
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Order',
    )

    discount = fields.Float(
        string='discount',
        help='discount in %',
        related='instalment_id.discount',
    )
    bank_discount = fields.Float(
        string='Bank discount',
        help='Bank discount in %',
        related='instalment_id.bank_discount',
    )

    discount_amount = fields.Float(
        string='discount amount',
        help='discount in $',
        compute='change_instalment_id',
        store=True,
    )

    clearing_date = fields.Date(
        string='Clearing Date',
        compute='compute_clearing_date',
        store=True,

    )

    @api.depends('instalment_id')
    def compute_clearing_date(self):
        for payment in self:
            if len(payment.instalment_id) and len(payment.instalment_id.payment_term_id):
                payment.clearing_date = payment.instalment_id.payment_term_id.compute(payment.amount, payment.payment_date)[0][0]
            else:
                payment.clearing_date = payment.payment_date 

    def _prepare_payment_moves(self):
        res = super()._prepare_payment_moves()
        return res
        all_moves_vals = []

        for payment in self:
            moves_vals = super()._prepare_payment_moves()

            if len(payment.instalment_id) and len(payment.instalment_id.payment_term_id):
                moves_vals['line_ids'][0]['date_maturity'] = payment.instalment_id.payment_term_id.compute(payment.amount,payment.payment_date)[0][0]

            all_moves_vals += moves_vals

        return all_moves_vals

    @api.onchange('magnet_bar')
    def _onchange_magnet_bar(self):
        if self.magnet_bar:
            try:
                track1, track2 = self.magnet_bar.split(';')
                cardnumber, name, data = track1.split('^')
                # to-do: add chksum
                self.card_number = cardnumber
            except ValueError:
                raise ValidationError(_('Could not parse track'))

    @api.onchange('journal_id')
    def _onchange_journal(self):
        res = super(AccountPayment, self)._onchange_journal()
        if len(self.sale_order_id):
            self.amount = self.sale_order_id.amount_residual
        return res

    @api.onchange('currency_id')
    def _onchange_currency(self):
        res = super(AccountPayment, self)._onchange_currency()
        if len(self.sale_order_id):
            self.amount = self.sale_order_id.amount_residual
        return res

    def action_register_sale_payment(self):
        active_ids = self.env.context.get('active_ids')

        if len(active_ids) != 1:
            raise ValidationError(_('Not Implemented'))
        if not active_ids:
            return ''

        sale_order = self.env['sale.order'].browse(active_ids)

        total_amount = sale_order.amount_total
        payment_amout = sum(sale_order.payment_ids.filtered(
                lambda x: x.state not in ['draft', 'cancelled']).mapped('amount'))

        amount = total_amount - payment_amout
        payment_type = 'inbound'
        partner_id = sale_order.partner_invoice_id.id

        # to-do : default Get
        new_context = dict(self.env.context).copy()

        new_context.update({'default_partner_id': partner_id, 'default_payment_type': payment_type, 'active_id': active_ids[0],
                            'active_ids': active_ids, 'default_sale_order_id': sale_order.id, 'default_amount': amount})
        return {
            'name': _('Register Payment'),
            'res_model': len(active_ids) == 1 and 'account.payment' or 'account.payment.register',
            'view_mode': 'form',
            'view_id': len(active_ids) != 1 and self.env.ref('account.view_account_payment_form_multi').id or self.env.ref('account.view_account_payment_invoice_form').id,
            'context': new_context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def draft_post(self):

        for rec in self:
            if rec.fee != 0.0:

                if len(rec.draft_invoice_ids):
                    fee_invoice_id = False
                    # to-do usar filterd
                    for invoice_id in rec.draft_invoice_ids:
                        if invoice_id == 'draft':
                            fee_invoice_id = invoice_id
                            break
                    if not fee_invoice_id:
                        raise ValidationError(_('Invoices not Draft'))
                    fee_invoice_id.invoice_line_ids = [(0, 0, {
                        'product_id': rec.instalment_id.product_id.id,
                        'quantity': 1,
                        'price_unit': rec.fee,
                        #'tax_ids'[:(6,0,[rec.instalment_id.product_id.id.tax_ids.ids])]
                        #'account_id'
                    })]

                rec.amount = rec.amount + rec.fee

        return super(AccountPayment, self).post()

    def post(self):
        for rec in self:
            if rec.fee != 0.0:
                if len(rec.sale_order_id):
                    if rec.instalment_id.product_id.taxes_id:
                        tax_amount = rec.instalment_id.product_id.taxes_id.compute_all(rec.fee)

                        # esto lo hago para restar el iva si no esta incluido
                        # en el precio
                        if tax_amount['total_included'] > rec.fee:
                            tax_amount = rec.instalment_id.product_id.taxes_id.with_context(force_price_include=True).compute_all(rec.fee)
                            amount = tax_amount['total_excluded']
                        else:
                            amount = tax_amount['total_included']
                    line_vals = []
                    line_vals.append({
                        'order_id': rec.sale_order_id.id,
                        'product_id': rec.instalment_id.product_id.id,
                        'product_uom_qty': 1,   
                        'price_unit': amount,
                        'is_financial_line': True,                        
                        'tax_id': [(6, 0, rec.instalment_id.product_id.taxes_id.ids)],
                        'sequence': 999,

                    })

                    if rec.discount_amount:
                        discount_amount = rec.discount_amount
                        if rec.instalment_id.product_id.taxes_id:
                            tax_amount = rec.instalment_id.product_id.taxes_id.compute_all(rec.discount_amount)
                            if tax_amount['total_included'] > rec.discount_amount:
                                tax_amount = rec.instalment_id.product_id.taxes_id.with_context(force_price_include=True).compute_all(rec.discount_amount)
                                discount_amount = tax_amount['total_excluded']
                            else:
                                discount_amount = tax_amount['total_included']

                        line_vals.append({
                            'order_id': rec.sale_order_id.id,
                            'product_id': rec.instalment_id.product_id.id,
                            'name': _("discount off %% %s") % rec.instalment_id.discount,
                            'product_uom_qty': 1,
                            'price_unit': 0 - discount_amount,
                            'is_financial_line': True,
                            'tax_id': [(6, 0, rec.instalment_id.product_id.taxes_id.ids)],
                            'sequence': 999,
                        })
                    if rec.instalment_id.bank_discount:
                        bank_discount = (amount * ((100 + rec.instalment_id.bank_discount)/100))
                        line_vals.append({
                            'order_id': rec.sale_order_id.id,
                            'display_type': 'line_note',
                            'name': _("bank discount off %% %s %s") % (rec.instalment_id.bank_discount, bank_discount),
                            'is_financial_line': True,
                            'sequence': 999,

                        })
                    line = self.env['sale.order.line'].create(line_vals)
                    line[0].price_total = rec.fee
                elif len(rec.invoice_ids):
                    fee_invoice_id = False
                    # to-do usar filterd
                    fee_invoice_id = rec.invoice_ids.filtered(
                        lambda x: x.state == 'draft')

                    if not fee_invoice_id:
                        fee_invoice_id = self.env['account.move'].create(
                            {
                                'type': rec.invoice_ids[0].type,
                                'journal_id': rec.invoice_ids[0].journal_id.id,
                                'partner_id': rec.invoice_ids[0].partner_id.id,
                                'invoice_user_id': rec.invoice_ids[0].invoice_user_id.id,
                                'team_id': rec.invoice_ids[0].team_id.id,
                                #'invoice_incoterm_id': rec.invoice_ids[0].incoterm_id.id,

                            }
                        )
                    else:
                        fee_invoice_id = fee_invoice_id[0]

                    fee_invoice_id.invoice_line_ids = [(0, 0, {
                        'product_id': rec.instalment_id.product_id.id,
                        'quantity': 1,
                        'price_unit': rec.fee,
                        'tax_ids': [(6, 0, rec.instalment_id.product_id.taxes_id.ids)]
                    })]

                    rec.invoice_ids = [(4, fee_invoice_id.id)]
                    if fee_invoice_id.state == 'draft':
                        fee_invoice_id.action_post()
                rec.amount = rec.amount + rec.fee - rec.discount_amount

        ret = super(AccountPayment, self).post()
        if len(rec.sale_order_id):
            return rec.sale_order_id.action_register_sale_payment()
        return ret

    @api.depends('instalment_id', 'amount')
    def change_instalment_id(self):
        # self.ensure_one()
        for record in self:
            if len(record.instalment_id):
                if record.instalment_id.coefficient:
                    tax_amount = 0.0
                    amount = record.amount 
                    discount_amount = 0.0
                    if record.instalment_id.discount:
                        discount_amount = (amount * (self.instalment_id.discount/100))
                        record.discount_amount = discount_amount
                    if record.instalment_id.product_id.taxes_id:

                        tax_amount = record.instalment_id.product_id.taxes_id.compute_all(
                            amount)

                    #self.fee = self.instalment_id.fee
                    record.fee = amount * (self.instalment_id.coefficient - 1.0)

                    #* (1 + tax_amount / 100)
                    record.total_amount = amount + record.fee - discount_amount
                else:
                    record.fee = 0
                    record.discount_amount = 0
                    record.total_amount = record.amount
            else:
                record.fee = 0
                record.discount_amount = 0
                record.total_amount = record.amount

    @api.model
    def default_get(self, default_fields):
        rec = super(AccountPayment, self).default_get(default_fields)
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        active_model = self._context.get('active_model')
        # Check for selected sale order id
        if not active_ids or active_model != 'sale.order':
            return rec

        order = self.env['sale.order'].browse(active_ids)

        # .filtered(lambda move: move.is_invoice(include_receipts=True))
        amount = order[0].amount_residual
        rec.update({
            'currency_id': order[0].currency_id.id,
            'amount': abs(amount),
            'payment_type': 'inbound' if amount > 0 else 'outbound',
            'partner_id': order[0].partner_invoice_id.id,
            'sale_order_id': order[0].id,
        })
        return rec


"""
account.move
    def action_invoice_register_payment(self):
        return self.env['account.payment']\
            .with_context(active_ids=self.ids, active_model='account.move', active_id=self.id)\
            .action_register_payment()
        """
