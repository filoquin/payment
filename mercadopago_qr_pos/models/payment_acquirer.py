from odoo import fields, models, _

class PaymentAcquirer(models.Model):

    _inherit = 'payment.acquirer'

    def mp_qr_pos_transaction(self, data):
        if data['configId']:
            config_id = self.env['pos.config'].browse(data['configId'])
            data['store_external_id'] = config_id.mp_store_id.external_id
            data['pos_external_id'] = config_id.mp_external_id
        return self.create_order(data)