# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import datetime
from odoo.exceptions import UserError, ValidationError
from odoo.osv.expression import AND

import logging
_logger = logging.getLogger(__name__)

class ReportSaleDetails(models.AbstractModel):

    _name = 'report.cash_control.report_saledetails'
    _description = 'Cash Control Details'


    @api.model
    def get_sale_details(self, date_start=False, date_stop=False, config_ids=False, session_ids=False):
        """ Serialise the orders of the requested time period, configs and sessions.

        :param date_start: The dateTime to start, default today 00:00:00.
        :type date_start: str.
        :param date_stop: The dateTime to stop, default date_start + 23:59:59.
        :type date_stop: str.
        :param config_ids: Pos Config id's to include.
        :type config_ids: list of numbers.
        :param session_ids: Pos Config id's to include.
        :type session_ids: list of numbers.

        :returns: dict -- Serialised sales.
        """
        #domain = [('state', 'in', ['paid','invoiced','done'])]
        domain = [('state', 'not in', ['draft'])]

        if (session_ids):
            domain = AND([domain, [('session_id', 'in', session_ids)]])
        else:
            if date_start:
                date_start = fields.Datetime.from_string(date_start)
            else:
                # start by default today 00:00:00
                user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
                today = user_tz.localize(fields.Datetime.from_string(fields.Date.context_today(self)))
                date_start = today.astimezone(pytz.timezone('UTC'))

            if date_stop:
                date_stop = fields.Datetime.from_string(date_stop)
                # avoid a date_stop smaller than date_start
                if (date_stop < date_start):
                    date_stop = date_start + timedelta(days=1, seconds=-1)
            else:
                # stop by default today 23:59:59
                date_stop = date_start + timedelta(days=1, seconds=-1)

            domain = AND([domain,
                [('date_order', '>=', fields.Datetime.to_string(date_start)),
                ('date_order', '<=', fields.Datetime.to_string(date_stop))]
            ])

            if config_ids:
                domain = AND([domain, [('config_id', 'in', config_ids)]])

        orders = self.env['sale.order'].search(domain)

        user_currency = self.env.company.currency_id

        total = 0.0
        products_sold = {}
        taxes = {}
        for order in orders:
            if user_currency != order.pricelist_id.currency_id:
                total += order.pricelist_id.currency_id._convert(
                    order.amount_total, user_currency, order.company_id, order.date_order or fields.Date.today())
            else:
                total += order.amount_total
            currency = order.cash_control_session_id.currency_id

            for line in order.order_line:
                key = (line.product_id, line.price_total, line.discount)
                products_sold.setdefault(key, 0.0)
                products_sold[key] += line.product_uom_qty

                if line.tax_id:
                    taxes.setdefault(line.tax_id[0].id, {'name': line.tax_id[0].name, 'tax_amount':0.0, 'base_amount':0.0})
                    taxes[line.tax_id[0].id]['tax_amount'] += line.price_tax
                    taxes[line.tax_id[0].id]['base_amount'] += line.price_subtotal
                else:
                    taxes.setdefault(0, {'name': _('No Taxes'), 'tax_amount':0.0, 'base_amount':0.0})
                    taxes[0]['base_amount'] += line.price_subtotal

        payment_ids = self.env["account.payment"].search([('sale_order_id', 'in', orders.ids)]).ids
        if payment_ids:
            self.env.cr.execute("""
                SELECT method.name, sum(amount) total
                FROM account_payment AS payment,
                     account_journal AS method
                WHERE payment.journal_id = method.id
                    AND payment.id IN %s
                GROUP BY method.name
            """, (tuple(payment_ids),))
            payments = self.env.cr.dictfetchall()
        else:
            payments = []

        return {
            'currency_precision': user_currency.decimal_places,
            'total_paid': user_currency.round(total),
            'payments': payments,
            'company_name': self.env.company.name,
            'taxes': list(taxes.values()),
            'products': sorted([{
                'product_id': product.id,
                'product_name': product.name,
                'code': product.default_code,
                'quantity': qty,
                'price_unit': price_total,
                'discount': discount,
                'uom': product.uom_id.name
            } for (product, price_total, discount), qty in products_sold.items()], key=lambda l: l['product_name'])
        }

    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        configs = self.env['cash.control.config'].browse(data['config_ids'])
        data.update(self.get_sale_details(data['date_start'], data['date_stop'], configs.ids))
        return data
