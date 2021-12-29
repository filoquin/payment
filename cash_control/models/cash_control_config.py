# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import datetime
import pytz
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class CashControlConfig(models.Model):

    _name = "cash.control.config"
    _description = "Cash Control Config"

    state = fields.Selection(
        [('draft', 'Draft'), ('active', 'Active'), ('cancel', 'Cancel')],
        default='draft',
        string="State"
    )
    name = fields.Char(
        string='Name',
        required=True,
    )
    code = fields.Char(
        string='Code',
        required=True,
    )
    store_id = fields.Many2one(
        'res.store',
        string="Store"
    )
    payment_journal_ids = fields.Many2many(
        comodel_name='account.journal',
        relation='config_journal_rel',
        column1='config_id',
        column2='journal_id',
        string='Payment Method',
        domain=[('type', 'in', ('bank', 'cash'))],
        default=lambda self: self.env['account.journal'].search(
            [('multi_store', '=', True)])
    )
    sale_journal_ids = fields.Many2many(
        comodel_name='account.journal',
        relation='config_sale_journal_rel',
        column1='config_id',
        column2='journal_id',
        string='Sale Journals',
        domain=[('type', '=', 'sale')]
    )
    session_sequence_id = fields.Many2one(
        'ir.sequence',
        string='Session Sequence',
        readonly=True,
        copy=False
    )
    sequence_id = fields.Many2one(
        'ir.sequence',
        string='Receipt Sequence',
        readonly=True,
        copy=False
    )
    current_session_id = fields.Many2one(
        'cash.control.session',
        string='Current Session',
        copy=False
    )
    session_state = fields.Selection(
        [('draft', 'Draft'), ('opened', 'Opened'), ('closed', 'Closed')],
        string='State',
        related="current_session_id.state"
    )
    session_state_info = fields.Selection(
        [('draft', 'Draft'), ('opened', 'Opened'), ('closed', 'Closed')],
        string='State',
        compute='_compute_session_state'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        readonly=False,
        default=lambda self: self.env.user.company_id.currency_id.id
    )
    default_cashbox_id = fields.Many2one(
        'account.bank.statement.cashbox', string='Default Balance')
    last_session_closing_cash = fields.Float(compute='_compute_last_session')
    last_session_closing_date = fields.Date(compute='_compute_last_session')
    last_session_closing_cashbox = fields.Many2one(
        'account.bank.statement.cashbox', compute='_compute_last_session')
    session_ids = fields.One2many(
        'cash.control.session', 'config_id', string='Sessions')

    statement_balance_start = fields.Monetary(
        related='current_session_id.statement_id.balance_start',
        string="Starting Balance",
        help="Total of opening cash control lines.",
        readonly=True
    )
    statement_total_entry_encoding = fields.Monetary(
        related='current_session_id.statement_total_entry_encoding',
        string='Total Cash Transaction',
        readonly=True,
        help="Total of all paid sales orders")
    statement_balance_end = fields.Monetary(
        related='current_session_id.statement_balance_end',
        string="Theoretical Closing Balance",
        help="Sum of opening balance and transactions.",
        readonly=True)


    statement_difference = fields.Monetary(
        related='current_session_id.statement_difference',
        string='Difference',
        help="Difference between the theoretical closing balance and the real closing balance.",
        readonly=True)
    statement_balance_end_real = fields.Monetary(
        related='current_session_id.statement_id.balance_end_real',
        string="Ending Balance",
        help="Total of closing cash control lines.",
        readonly=True
    )
    statement_balance_start = fields.Monetary(
        related='current_session_id.statement_id.balance_start',
        string="Starting Balance",
        help="Total of opening cash control lines.",
        readonly=True
    )
    amount_authorized_diff = fields.Float('Amount Authorized Difference',
                                          help="This field depicts the maximum difference allowed between the ending balance and the theoretical cash when "
                                          "closing a session, for non-POS managers. If this maximum is reached, the user will have an error message at "
                                          "the closing of his session saying that he needs to contact his manager.")
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        required=True,
        default=lambda self: self.env.user.company_id
    )
    user_ids = fields.Many2many(
        'res.users',
        string='Responsibles',
    )
    is_acum_cash_control = fields.Boolean(
        'Es Caja Acumuladora'
    )
    is_main_cash_control = fields.Boolean(
        'Es Caja Principal'
    )
    statement_ids = fields.One2many(
        'account.bank.statement',
        related="current_session_id.statement_ids",
        string='Bank Statement',
        readonly=True
    )

    payment_summary_ids = fields.One2many(
        'cash.control.session.payment_summary',
        related="current_session_id.payment_summary_ids",
        string='Payments',
    )
    journal_id = fields.Many2one(
        'account.journal',
        related='current_session_id.statement_id.journal_id',
        string="Statement Journal",
        readonly=True
    )
    transfer_pendientes = fields.Boolean(

    )
    active = fields.Boolean(
        string='Active',
        default=True
    )

    last_balance_end_real = fields.Float(
        string='Last balance',
        compute='_compute_last_balance_end_real'
    )

    def _compute_last_balance_end_real(self):
        for config_id in self:
            if len(config_id.current_session_id):
                config_id.last_balance_end_real = config_id.current_session_id.statement_id.balance_end_real
            else:

                last_stmt = self.env['account.bank.statement'].search(
                        [('cash_control_session_id.config_id', '=', config_id.id)],
                        order='date desc, id desc', limit=1)

                config_id.last_balance_end_real = last_stmt and last_stmt.balance_end_real or 0

    def _compute_session_state(self):
        for config in self:
            if len(config.current_session_id):
                config.session_state_info = config.current_session_id.state
            else:
                config.session_state_info = 'closed'                

    @api.model
    def create(self, values):
        res = super(CashControlConfig, self).create(values)

        res.session_sequence_id = self.env['ir.sequence'].sudo().create({
            'name': 'session %s' % values['code'],
            'padding': 6,
            'prefix': "%s-" % values['code'],
            'code': "session_%s" % res.id,
        }).id

        res.sequence_id = self.env['ir.sequence'].sudo().create({
            'name': 'receipt %s' % values['code'],
            'padding': 6,
            'prefix': "%s-" % values['code'],
            'code': "receipt_%s" % res.id,
        }).id

        return res

    def write(self, values):
        if not self.user_has_groups('ba_base.blancoamor_administacion') \
           and 'current_session_id' not in values.keys() \
           and 'transfer_pendientes' not in values.keys():
            group = self.env.ref('ba_base.blancoamor_administacion').sudo()
            raise UserError(_(
                'Only users with "%s" group can write a cash control config') % (
                group.name))
        return super().write(values)

    def unlink(self):
        self.sequence_id.unlink()
        self.session_sequence_id.unlink()
        return super(CashControlConfig, self).unlink()

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {},
                       name=_('%s (copy)') % self.name,
                       code=_('%s (copy)') % self.code,
                       session_sequence_id=False,
                       sequence_id=False)
        return super(CashControlConfig, self).copy(default=default)

    def set_active(self):
        self.state = 'active'

    def set_cancel(self):
        self.state = 'cancel'

    def set_draft(self):
        self.state = 'draft'

    def open_session(self):
        # poner boton en vista tree
        # abrir wizard de apertura de caja
        # crear session
        session = {
            'config_id': self.id
        }
        session_id = self.env['cash.control.session'].create(session)
        self.current_session_id = session_id.id
        transfer_id = self.env['cash.control.transfer.cash'].search([
            ('dest_cash_control_id', '=', self.id),
            ('state', '=', 'transfer')])
        if transfer_id:
            self.transfer_pendientes = True
        return True

    def check_user(self):
        if self.env.uid not in self.current_session_id.user_ids.ids:
            raise UserError(_(
                'You are not the responsible of the cash control %s (%s)') % (
                self.name, self.current_session_id.user_ids[0].name))

    def close_session(self):
        # cerrar session
        # concialiacion?
        self.check_user()
        self.current_session_id.action_session_close()
        self.current_session_id = False
        self.transfer_pendientes = False
        return True

    def open_cashbox_pos(self):
        if not self.session_state:
            self.open_session()
        self.check_user()
        return self.current_session_id.open_cashbox_pos()

    @api.depends('session_ids')
    def _compute_last_session(self):
        PosSession = self.env['cash.control.session']
        for pos_config in self:
            session = PosSession.search_read(
                [('config_id', '=', pos_config.id), ('state', '=', 'closed')],
                ['statement_balance_end_real', 'date_end', 'statement_id'],
                #order="date_end desc", limit=1)
                order="id desc", limit=1)
            if session:
                timezone = pytz.timezone(self._context.get(
                    'tz') or self.env.user.tz or 'UTC')
                if not (session[0]['date_end']):
                    pos_config.last_session_closing_cash = 0
                    pos_config.last_session_closing_date = False
                    pos_config.last_session_closing_cashbox = False
                    continue

                pos_config.last_session_closing_date = session[
                    0]['date_end'].astimezone(timezone).date()
                if session[0]['statement_id']:
                    pos_config.last_session_closing_cash = session[
                        0]['statement_balance_end_real']
                    pos_config.last_session_closing_cashbox = self.env[
                        'account.bank.statement'].browse(session[0]['statement_id'][0]).cashbox_end_id
                else:
                    pos_config.last_session_closing_cash = 0
                    pos_config.last_session_closing_cashbox = False
            else:
                pos_config.last_session_closing_cash = 0
                pos_config.last_session_closing_date = False
                pos_config.last_session_closing_cashbox = False
