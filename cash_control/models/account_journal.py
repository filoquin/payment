##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, api, fields


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    multi_store = fields.Boolean(
        'Usar en multiples locales',
    )

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        user = self.env.user
        if 'filter_journals' not in self.env.context.keys():
            return super()._search(args, offset, limit, order, count=count, access_rights_uid=access_rights_uid)
        # if superadmin, do not apply
        administacion = self.user_has_groups('ba_base.blancoamor_administacion')
        if not self.env.is_superuser() or not administacion:
            session_ids = self.env['cash.control.session'].search(
                [('user_ids', 'in', self.env.user.id), ('state', '=', 'opened')])
            if session_ids:
                try:
                    if args[0][2]:
                        args = [(args[0][0], args[0][1], args[0][2] + session_ids[0].payment_journal_ids.ids)]
                except:
                    None
                args += ['|', ('id', 'in', session_ids[0].payment_journal_ids.ids), ('type', 'not in', ['cash', 'bank'])]
            elif self.user_has_groups('sales_team.group_sale_manager'):
                args += ['|', ('store_id', '=', False),
                         ('store_id', 'child_of', [user.store_id.id])]
            else:
                # Si no tiene sesion abierta y no pertenece al grupo Ventas /
                # Admin -> no ve ningun journal
                args = [('id', '>', 999999)]
        return super()._search(args, offset, limit, order, count=count, access_rights_uid=access_rights_uid)
