# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _default_cash_control_session_id(self):
        session = self.env['cash.control.session'].search([
            ('user_ids', 'in', self.env.uid),
            ('state', '=', 'opened')
        ])
        if not session:
            return False
            # raise ValidationError(_("There is not open cash session for de the current user. Please open a cash session"))
        return session.id

    refund_move_lines_ids = fields.Many2many(
        'account.move.line',
        string='refund lines',
        copy=False,
    )

    cash_control_session_id = fields.Many2one(
        'cash.control.session',
        string='Session',
        copy=False,
        default=_default_cash_control_session_id
    )
    config_id = fields.Many2one(
        'cash.control.config',
        related='cash_control_session_id.config_id',
        string="Cash Control",
        readonly=False
    )

    def add_credit_note(self):
        self.ensure_one()

        view_id = self.env.ref('cash_control.add_credit_note_form').id

        view = {
            'name': "Ventas",
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'sale.order.add_credit_note',
            'res_id': False,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'context': {'default_order_id': self.id}
        }
        return view

    def invoice_and_conciled(self):

        report_action = super().invoice_and_conciled()
        if self.refund_move_lines_ids:
            _logger.info(report_action)
            invoice = self.env['account.move'].browse(report_action['context']['active_ids'][0])
            for line_id in self.refund_move_lines_ids:
                invoice.js_assign_outstanding_line(line_id.id)
     
        return report_action
    
    @api.depends('payment_ids', 'order_line', 'refund_move_lines_ids')
    def _compute_amount(self):
        for so in self:

            payment_amout = sum(so.payment_ids.filtered(
                lambda x: x.state not in ['draft', 'cancelled'] and \
                    x.payment_type_copy != 'outbound').mapped('amount'))
            credit_note_amout = sum(so.payment_ids.filtered(
                lambda x: x.state not in ['draft', 'cancelled'] and \
                    x.payment_type_copy == 'outbound').mapped('amount'))
            refund_move_lines_amout = sum(so.refund_move_lines_ids.mapped('amount_residual')) * -1
            so.amount_residual = so.amount_total - payment_amout + credit_note_amout - refund_move_lines_amout

    def _create_invoices(self, grouped=False, final=False):

        session = self.env['cash.control.session'].search([
            ('user_ids', 'in', self.env.uid),
            ('state', '=', 'opened')
        ])
        if len(session): 
            if not len(session.config_id.sale_journal_ids):
                raise UserError(_('No hay diario de ventas activo'))
            journal_id = session.config_id.sale_journal_ids[0].id
            return super(SaleOrder, self.with_context(
                default_journal_id=journal_id,
                cash_control_session_id=session.id
            ))._create_invoices(grouped, final)

        return super()._create_invoices(grouped, final)
