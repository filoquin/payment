odoo.define('pos_card_instalment.models', function (require) {
var models = require('point_of_sale.models');
var screens = require('point_of_sale.screens');

// Agrego los campos en la tarjeta
models.load_fields('pos.payment.method', ['card_id','instalment_ids']);

// Obtengo las cuotas y las asifno a sus metodos de pago
models.load_models([{
    model: 'account.card.instalment',
    fields: ['card_id','name','instalment','product_id','amount','coefficient','discount','bank_discount','active','card_type'],
    domain: function(self){ return [['card_id', '!=', false]]; },
    loaded: function(self, instalment_ids) {
        let instalment_by_card = {}
        _.each(instalment_ids, function(instalment_id,index) {
            instalment_by_card[instalment_id.card_id[0]] = instalment_by_card[instalment_id.card_id[0]] || [] ;
            instalment_by_card[instalment_id.card_id[0]].push(instalment_id);
        })

        _.each(self.payment_methods_by_id, function(payment_method,index) {
            if (payment_method.card_id){
                self.payment_methods_by_id[index].instalments = instalment_by_card[payment_method.card_id[0]]
            }
        });

    }
},
]);

// Modifico la pantalla de pago
screens.PaymentScreenWidget.include({
    start:function(){
            this._super();
            var self = this;
            console.log('start');
    },

    show: function(){
            this._super();
            console.log('show');
    },
    render_payment_terminal: function() {
        var self = this;
        console.log('Render');
    },

});

});
