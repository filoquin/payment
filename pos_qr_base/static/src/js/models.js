odoo.define('pos_qr_base.models', function (require) {
var models = require('point_of_sale.models');
var PaymentQR = require('pos_qr_base.payment');

models.register_payment_method('qr', PaymentQR);
models.load_fields('pos.payment.method', ['use_qr','qr_method','qr_image','pos_qr_image']);
models.load_fields('pos.payment', ['tx_ids'])

});

/*
  var _super = models.Paymentline;
  models.Paymentline = models.Paymentline.extend({
    export_as_JSON: function(attributes,options){
        var json = _super.prototype.export_as_JSON.apply(this,arguments);

        json['tx_ids']
                    tax_ids: [[6, false, _.map(this.get_applicable_taxes(), function(tax){ return tax.id; })]],

        initialize.to_invoice = options.pos.config.always_invoice;
        return json;

    },
  });

*/