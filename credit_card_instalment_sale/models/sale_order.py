from odoo import models, api, fields, _
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    payment_ids = fields.One2many(
        'account.payment',
        'sale_order_id',
        string='Payments',
    )
    amount_residual = fields.Monetary(
        string='Amount Due',
        compute='_compute_amount'
    )

    @api.depends('payment_ids', 'order_line')
    def _compute_amount(self):
        for so in self:

            payment_amout = sum(so.payment_ids.filtered(
                lambda x: x.state not in ['draft', 'cancelled'] and \
                    x.payment_type_copy != 'outbound').mapped('amount'))
            credit_note_amout = sum(so.payment_ids.filtered(
                lambda x: x.state not in ['draft', 'cancelled'] and \
                    x.payment_type_copy == 'outbound').mapped('amount'))
            so.amount_residual = so.amount_total - payment_amout + credit_note_amout

    def action_register_sale_payment(self):
        self.ensure_one()
        self._compute_amount()
        if self.amount_residual > 1.0:
            return self.env['account.payment']\
                .with_context(active_ids=self.ids, active_model='sale.order', active_id=self.id)\
                .action_register_sale_payment()
        elif self.invoice_status == 'to invoice':
            if self.amount_residual != 0:
                round_product_id = self.env['ir.config_parameter'].get_param('round_product_id', False)
                if round_product_id:
                    round_product = self.env['product.product'].browse(int(round_product_id))
                    self.order_line = [(0, 0, {
                                'product_id': round_product.id,
                                'name': _("Round"),
                                'product_uom_qty': 1,
                                'price_unit': self.amount_residual * -1,
                                'is_financial_line': True,
                                'sequence': 999,
                                'tax_id': [(6, 0, round_product.taxes_id.ids)]
                            })]

            journal_id = self.config_id.sale_journal_ids[0].id
            self.with_context(default_journal_id=journal_id)._create_invoices()
            try:
                for invoice in self.invoice_ids:
                    # confirma la factura
                    invoice.action_post()
                    for payment in self.payment_ids:
                        move_line = self.env['account.move.line'].search([
                            ('payment_id', '=', payment.id),
                            ('debit', '=', 0),
                        ])
                        # concilia la factura con los pagos
                        invoice.js_assign_outstanding_line(move_line.id)
                    # devuelve el pdf de la factura
                    self.inovice_status = 'invoiced'
                    return self.env.ref('account.account_invoices').report_action(invoice)
            except Exception as e:
                self.message_post(body=e)

    def copy_data(self, default=None):
        if default is None:
            default = {}
        if 'order_line' not in default:
            default['order_line'] = [(0, 0, line.copy_data()[0]) for line in self.order_line.filtered(lambda l: not l.is_downpayment and not l.is_financial_line)]
        else:
            default['order_line'] = [(0, 0, line) for line in default['order_line'].filtered(lambda l: not l.is_downpayment and not l.is_financial_line)]
        return super(SaleOrder, self).copy_data(default)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_financial_line = fields.Boolean(
        string='Financial line',
    )


