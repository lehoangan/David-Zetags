openerp.z_customer = function (instance) {
    instance.web.z_customer = instance.web.z_customer || {};

    instance.web.z_customer.show_popup_customer_alert = instance.web.View.extend(instance.web.FormView, {
        init: function(parent, dataset, view_id, options) {
        	var self = this;
        	this._super(parent);
        },
        
        on_button_edit: function() {
        	throw new Error(_.str.sprintf( _t("Wrong on change format: %s"), _.str.trim(this.datarecord.id); ));
	        return this.to_edit_mode();
	    },
        
    });
};