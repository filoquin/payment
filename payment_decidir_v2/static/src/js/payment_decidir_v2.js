odoo.define('payment_decidir_v2.payment', function (require) {
"use strict";


var core = require('web.core');
var config = require('web.config');
var concurrency = require('web.concurrency');
var publicWidget = require('web.public.widget');
var qweb = core.qweb;
var Dialog = require('web.Dialog');
var PaymentForm = require('payment.payment_form');

PaymentForm.include({
    // TODO: Esto deberia heredar
    events: {
        'submit': 'onSubmit',
        'click #o_payment_form_pay': 'payEvent',
        'click #o_payment_form_add_pm': 'addPmEvent',
        'click button[name="delete_pm"]': 'deletePmEvent',
        'click .o_payment_form_pay_icon_more': 'onClickMorePaymentIcon',
        'click .o_payment_acquirer_select': 'radioClickEvent',
        "click .payment_dv2_start": "_decidir_start_payment",
    },

    _decidir_start_payment : function(event){
        $($(event.currentTarget)).addClass('active');
        let instalment_id = $(event.currentTarget).data('instalment_id');
        let acquirer_id = $(event.currentTarget).data('acquirer_id');
        let fee = $(event.currentTarget).data('fee' ) | 0;
        let amount = $(event.currentTarget).data('amount');
        let base_amount = $(event.currentTarget).data('base-amount');
        let method = $(event.currentTarget).data('method');
        let selected_text = $(event.currentTarget).text();
        $('input[name=instalment_id]').val(instalment_id);
        $('input[name=method]').val(method);
        $('input[name=amount]').val(amount);
        $('input[name=base_amount]').val(base_amount);
        $('input[name=fees]').val(fee);
        $('.decidir_v2_method_name').hide(100).html(selected_text).show(100);


      },
    /**
    * @override
    */
    payEvent: function (ev) {

        ev.preventDefault();
        var $checkedRadio = this.$('input[type="radio"]:checked');

        if ($checkedRadio.length === 1 &&  $checkedRadio.data('provider') === 'decidir_v2') {
            this._decidir_get_token($checkedRadio.data('acquirer-id'));        

            return false
        } else {
            return this._super.apply(this, arguments);
        }
    },
    show_error_dialog: function(title, text){
          new Dialog(null, {
                        title: title,
                size: 'medium',
                $content: "<p>"+ text +"</p>" ,
                buttons: [
                {text: 'Ok', close: true}]}).open();            

    },
    _decidir_validate_form: function(){
        if (!$("input[name=instalment_id]").val()){
          this.show_error_dialog('Atención',"Debe elegir un metodo de pago");
            return false;
        }
        return true;

    },

    _decidir_get_token: function(acquirer){
        if (!this._decidir_validate_form()){
            return ;
        } 
        var form = document.querySelector('.o_payment_form');

        const decidir_url =  $("input[name=decidir_url]").val()
        const instalment_id =  $("input[name=instalment_id]").val()
        const publicApiKey = $("input[name=decidir_public_key]").val();

        const inhabilitarCS = true;
        const decidir = new Decidir(decidir_url, inhabilitarCS);
        let base_amount = $("input[name=base_amount]").val();
        let fee = $("input[name=fees]").val()
        let amount = $("input[name=amount]").val()
        let decidir_order_id = $("input[name=decidir_order_id]").val()

        decidir.setPublishableKey(publicApiKey);

        let self = this; 
        decidir.createToken(form, function(status, response){
           if (status != 200 && status != 201) {
                 let error =response['error'].map(function(obj){
                     return obj['error']['message']
                 }) 
              self.show_error_dialog('Decidir',error.join('<br/>'));
           } else {
            self._rpc({
                    route: "/shop/cart/decidirv2_make_payment",
                    params: {
                        acquirer_id:acquirer, 
                        instalment_id: instalment_id,
                        token : response.id,
                        status : response.status,
                        card_number_length : response.card_number_length,
                        date_created : response.date_created,
                        bin : response.bin,
                        end_string : response.last_four_digits,
                        security_code_length : response.security_code_length,
                        expiration_month : response.expiration_month,
                        expiration_year : response.expiration_year,
                        date_due : response.date_due,
                        type : response.type,
                        number : response.number,
                        amount: amount,
                        base_amount: base_amount,
                        fee: fee,
                        decidir_order_id: decidir_order_id,
                    },
                }).then(function (data) {
                    if(data['state']=='ok'){
                        window.location.href = data['portal_url'];
                    } else {
                        window.location.href = '/shop/cart/decidirv2_ok';
                    };
                });
               let new_token = response.id;
               console.log (response)    
           }

        });
    },

    /**
     * @override
     */
    addPmEvent: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        var $checkedRadio = this.$('input[type="radio"]:checked');

        // first we check that the user has selected a decidir_v2 as add payment method
        if ($checkedRadio.length === 1 && this.isNewPaymentRadio($checkedRadio) && $checkedRadio.data('provider') === 'decidir_v2') {

            console.log('cli');

        } else {
            this._super.apply(this, arguments);
        }
    },    
});


});
