openerp.z_customer = function(instance){
    var _t = instance.web._t,
        _lt = instance.web._lt;

    instance.web.FormView = instance.web.FormView.extend({

        on_button_edit: function() {
            if (this.datarecord.alert) {
                alert(_.str.sprintf(_t("%s"), _.str.trim(this.datarecord.alert)));
            } else {
                if (this.datarecord.partner_id) {
                    new instance.web.Model('res.partner').call('read', [this.datarecord.partner_id[0], ['alert']]).then(function (results) {
                                 if (results['alert']) {
                                     alert(_.str.sprintf(_t("%s"), _.str.trim(results['alert'])));
                                 }
                    });
                };
            };
            return this.to_edit_mode();
        },

        on_button_save: function(e) {
            var self = this;
            if (this.datarecord.alert) {
                alert(_.str.sprintf(_t("%s"), _.str.trim(this.datarecord.alert)));
            } else {
                if (this.datarecord.partner_id) {
                    new instance.web.Model('res.partner').call('read', [this.datarecord.partner_id[0], ['alert']]).then(function (results) {
                                 if (results['alert']) {
                                     alert(_.str.sprintf(_t("%s"), _.str.trim(results['alert'])));
                                 }
                    });
                };
            };
            $(e.target).attr("disabled", true);
            return this.save().done(function(result) {
                self.trigger("save", result);
                self.reload().then(function() {
                    self.to_view_mode();
                    var parent = self.ViewManager.ActionManager.getParent();
                    if(parent){
                        parent.menu.do_reload_needaction();
                    }
                });
            }).always(function(){
                $(e.target).attr("disabled", false);
            });
        },

    });

    instance.web.form.WidgetButton = instance.web.form.WidgetButton.extend({

        on_click: function() {
            var self = this;
            if (this.view.datarecord.alert) {
                alert(_.str.sprintf(_t("%s"), _.str.trim(this.view.datarecord.alert)));
            } else {
                if (this.view.datarecord.partner_id) {
                    new instance.web.Model('res.partner').call('read', [this.view.datarecord.partner_id[0], ['alert']]).then(function (results) {
                                 if (results['alert']) {
                                     alert(_.str.sprintf(_t("%s"), _.str.trim(results['alert'])));
                                 }
                    });
                };
            };
            this.force_disabled = true;
            this.check_disable();
            this.execute_action().always(function() {
                self.force_disabled = false;
                self.check_disable();
            });
        },
    });

};