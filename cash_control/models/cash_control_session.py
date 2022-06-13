# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class CashControlSession(models.Model):

    _name = "cash.control.session"
    _description = "Cash Control Session"
    _inherit = ["mail.thread"]
    _order = "id desc"

    name = fields.Char(
        string="Session ID",
    )
    user_ids = fields.Many2many(
        "res.users",
        string="Responsibles",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("opened", "Opened"),
            ("closing_control", "Closing Control"),
            ("closed", "Closed"),
        ],
        string="State",
        default="draft",
    )
    config_id = fields.Many2one(
        "cash.control.config",
        string="Cash Control Config",
    )
    date_start = fields.Datetime(
        string="Start",
    )
    date_end = fields.Datetime(
        string="End",
    )
    payment_journal_ids = fields.Many2many(
        comodel_name="account.journal",
        relation="session_journal_rel",
        column1="session_id",
        column2="journal_id",
        string="Payment Method",
        domain=[("type", "in", ("bank", "cash"))],
        # related="till_config_id.payment_journal_ids",
        # store=True,
    )
    statement_ids = fields.One2many(
        "account.bank.statement",
        "cash_control_session_id",
        string="Bank Statement",
        readonly=True,
    )
    statement_id = fields.Many2one(
        "account.bank.statement",
        string="Bank Statement",
        copy=False,
        readonly=True,
    )
    payment_ids = fields.One2many(
        "account.payment",
        "cash_control_session_id",
        string="Receipt",
    )
    sale_order_ids = fields.One2many(
        "sale.order",
        "cash_control_session_id",
        string="Orders",
    )
    statement_balance_end_real = fields.Monetary(
        related="statement_id.balance_end_real",
        string="Ending Balance",
        help="Total of closing cash control lines.",
        readonly=True,
    )
    statement_balance_start = fields.Monetary(
        related="statement_id.balance_start",
        string="Starting Balance",
        help="Total of opening cash control lines.",
        readonly=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="config_id.currency_id",
        string="Currency",
        readonly=False,
    )
    statement_total_entry_encoding = fields.Monetary(
        compute="_compute_cash_balance",
        string="Total Cash Transaction",
        readonly=True,
        help="Total of all paid sales orders",
    )
    statement_balance_end = fields.Monetary(
        compute="_compute_cash_balance",
        string="Theoretical Closing Balance",
        help="Sum of opening balance and transactions.",
        readonly=True,
    )
    statement_difference = fields.Monetary(
        compute="_compute_cash_balance",
        string="Difference",
        help="Difference between the theoretical closing balance and the real closing balance.",
        readonly=True,
    )

    payment_summary_ids = fields.One2many(
        "cash.control.session.payment_summary",
        "session_id",
        string="Payments",
    )
    previous_session_id = fields.Many2one(
        "cash.control.session",
        string="previous session",
        compute="compute_previous_session",
    )

    @api.depends("config_id")
    def compute_previous_session(self):
        for session in self:
            session_id = self.search(
                [
                    ("config_id", "=", session.config_id.id),
                    ("state", "=", "closed"),
                    ("id", "<", session.id),
                ],
                order="id desc",
                limit=1,
            )
            if session_id:
                session.previous_session_id = session_id.id

    @api.depends(
        "statement_ids", "payment_ids", "statement_balance_start", "statement_id"
    )
    def _compute_cash_balance(self):
        for session in self:
            cash_payment_method = session.statement_id.journal_id
            total_cash_payment = sum(
                session.payment_ids.filtered(
                    lambda payment: payment.journal_id == cash_payment_method
                ).mapped("amount")
            )
            extra = 0.0 if session.state == "closed" else total_cash_payment
            session.statement_total_entry_encoding = (
                session.statement_id.total_entry_encoding
            )
            session.statement_balance_end = (
                session.statement_balance_start + session.statement_total_entry_encoding
            )
            session.statement_difference = (
                session.statement_balance_end_real - session.statement_balance_end
            )

    @api.model
    def create(self, vals):
        # Agrego esto para la migracion de datos
        if "name" in vals and "pwodoo_sync" in self.env.context:
            config_id = self.env["cash.control.config"].search(
                [("id", "=", vals["config_id"])]
            )
            vals["payment_journal_ids"] = [
                (4, x.id) for x in config_id.payment_journal_ids
            ]

            vals["payment_summary_ids"] = [
                (0, 0, {"journal_id": journal.id})
                for journal in config_id.payment_journal_ids
            ]

            return super(CashControlSession, self).create(vals)

        vals["date_start"] = fields.Datetime.now()
        session_name = self.env["ir.sequence"].next_by_code(
            "session_%s" % vals["config_id"]
        )
        vals["name"] = session_name
        vals["state"] = "draft"
        statements = []
        config_id = self.env["cash.control.config"].search(
            [("id", "=", vals["config_id"])]
        )
        vals["payment_journal_ids"] = [(4, x.id) for x in config_id.payment_journal_ids]

        vals["payment_summary_ids"] = [
            (0, 0, {"journal_id": journal.id})
            for journal in config_id.payment_journal_ids
        ]
        statement = False
        for journal in config_id.payment_journal_ids.filtered(
            lambda journal: journal.type == "cash"
        ):
            statement = (
                self.env["account.bank.statement"]
                .with_context(
                    {"journal_id": journal.id if journal.type == "cash" else False}
                )
                .create(
                    {
                        "journal_id": journal.id,
                        "user_id": self.env.user.id,
                        "name": session_name,
                    }
                )
            )
            statement.button_open()
            statements.append(statement.id)
        if not statement:
            raise UserError(_("Su Caja no tiene ningun diario de efectivo asignado"))
        vals["statement_ids"] = [(6, 0, statements)]
        vals["statement_id"] = statement.id
        session_ids = self.search(
            [("user_ids", "in", self.env.user.id), ("state", "!=", "closed")]
        )
        if session_ids:
            raise UserError(
                _("The user %s already has an opened session" % (self.env.user.name))
            )
        if "user_ids" not in vals:
            vals["user_ids"] = [(4, self.env.user.id)]

        res = super(CashControlSession, self).create(vals)

        return res

    def open_cashbox_pos(self):
        self.ensure_one()
        # action = self.cash_register_id.open_cashbox_id()
        action = self.statement_id.open_cashbox_id()
        action["view_id"] = self.env.ref(
            "account.view_account_bnk_stmt_cashbox_footer"
        ).id
        action["context"]["pos_session_id"] = self.id
        action["context"]["default_pos_id"] = self.config_id.id
        return action

    def _validate_session(self):
        self.ensure_one()
        self.state = "closed"
        self.date_end = fields.Datetime.now()

    def _check_pos_session_balance(self):
        for session in self:
            for statement in session.statement_ids:
                if (statement != session.statement_id) and (
                    statement.balance_end != statement.balance_end_real
                ):
                    statement.write({"balance_end_real": statement.balance_end})

    def action_session_close(self):
        _logger.info("clossing session....")

        if abs(self.statement_difference) > self.config_id.amount_authorized_diff:
            # Only pos manager can close statements with statement_difference greater than amount_authorized_diff.
            # if not self.user_has_groups("point_of_sale.group_pos_manager"):
            #     raise UserError(_(
            #         "Your ending balance is too different from the theoretical cash closing (%.2f), "
            #         "the maximum allowed is: %.2f. You can contact your manager to force it."
            #     ) % (self.statement_difference, self.config_id.amount_authorized_diff))
            # else:
            #     return self._warning_balance_closing()
            raise UserError(
                _(
                    "Your ending balance is too different from the theoretical cash closing (%.2f), "
                    "the maximum allowed is: %.2f. You can contact your manager to force it."
                )
                % (self.statement_difference, self.config_id.amount_authorized_diff)
            )
        # odoo 12 - session - action_pos_session_close
        # Close CashBox
        self._check_pos_session_balance()
        company_id = self.config_id.company_id.id
        ctx = dict(self.env.context, force_company=company_id, company_id=company_id)
        ctx_notrack = dict(ctx, mail_notrack=True)
        for st in self.statement_ids:
            # TODO: CERRAR SOLO LOS STATEMENTS DE CASH, EL DE TARJETA ES COMPARTIDO ENTRE TODAS LAS SUCURSALES - 15 TARJETAS APROX.
            # VER COMO RESOLVER EL STATEMENT DE TARJETA QUE ES COMPARTIDO.
            if st.journal_id.type not in ["bank", "cash"]:
                raise UserError(
                    _(
                        "The journal type for your payment method should be bank or cash."
                    )
                )
            st.with_context(ctx_notrack).sudo().button_confirm_bank()
        return self._validate_session()


class CashControlSessionPaymentSummary(models.Model):

    _name = "cash.control.session.payment_summary"
    _description = "Cash Control Session summary"

    session_id = fields.Many2one(
        "cash.control.session",
        string="session_id",
    )
    journal_id = fields.Many2one(
        "account.journal",
        string="Journal_id",
    )
    amount = fields.Float(string="amount", compute="compute_amount")

    def compute_amount(self):
        session_ids = self.mapped("session_id")
        _logger.info(session_ids)
        vals = {}
        for session_id in session_ids:

            journal_ids = self.mapped("journal_id")
            amounts = self.env["account.payment"].read_group(
                [
                    ("journal_id", "in", journal_ids.ids),
                    ("cash_control_session_id", "=", session_id.id),
                ],
                ["amount:sum"],
                ["journal_id"],
            )
            for amount in amounts:
                vals[amount["journal_id"][0]] = amount["amount"]

            for sumary in self.filtered(
                lambda line: line.session_id.id == session_id.id
            ):
                sumary.amount = vals.get(sumary.journal_id.id, 0)
