odoo.define('pos_qr_base.models', function (require) {
var models = require('point_of_sale.models');
var PaymentQR = require('pos_qr_base.payment');

models.register_payment_method('qr', PaymentQR);
models.load_fields('pos.payment.method', ['use_qr','qr_method','qr_image','pos_qr_image']);
models.load_fields('pos.payment', ['tx_ids', 'tx_manual_aprove', 'tx_manual_authorization'])

});

