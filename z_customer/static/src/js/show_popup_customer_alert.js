openerp.z_customer = function(instance){
    var _t = instance.web._t,
        _lt = instance.web._lt;

    instance.web_kanban.KanbanView = instance.web_kanban.KanbanView.extend({

        on_record_moved : function(record, old_group, old_index, new_group, new_index) {
            if (record.record.payment_term.raw_value[0] == 4 &&
                new_group.value == 6 &&
                record.record.balance.raw_value > 0) {
                    alert('THIS CUSTOMER MUST PAY BEFORE DELIVERY');
            };

            var self = this;
            $.fn.tipsy.clear();
            $(old_group.$el).add(new_group.$el).find('.oe_kanban_aggregates, .oe_kanban_group_length').hide();
            if (old_group === new_group) {
                new_group.records.splice(old_index, 1);
                new_group.records.splice(new_index, 0, record);
                new_group.do_save_sequences();
            } else {
                old_group.records.splice(old_index, 1);
                new_group.records.splice(new_index, 0, record);
                record.group = new_group;
                var data = {};
                data[this.group_by] = new_group.value;
                this.dataset.write(record.id, data, {}).done(function() {
                    record.do_reload();
                    new_group.do_save_sequences();
                }).fail(function(error, evt) {
                    evt.preventDefault();
                    alert(_t("An error has occured while moving the record to this group: ") + data.fault_code);
                    self.do_reload(); // TODO: use draggable + sortable in order to cancel the dragging when the rcp fails
                });
            }
        },

    });

    instance.web.FormView = instance.web.FormView.extend({

        on_button_edit: function() {
            if (this.datarecord.alert) {
                alert(_.str.sprintf(_t("%s"), _.str.trim(this.datarecord.alert)));
            } else {
                if (this.datarecord.partner_id && this.datarecord.partner_id[0]) {
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
                if (this.datarecord.partner_id && this.datarecord.partner_id[0]) {
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
                if (this.view.datarecord.partner_id && this.view.datarecord.partner_id[0]) {
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