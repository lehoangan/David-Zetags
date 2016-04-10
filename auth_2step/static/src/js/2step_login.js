openerp.auth_2step = function(instance) {
    instance.auth_2step = instance.auth_2step || {};
    var _t = instance.web._t;

    instance.web.Login.include({
        start: function() {
            var self = this;
            this.twostep_enabled = false;
            return this._super().always(function() {

                // Switches the login box to the select mode whith mode == [default|signup|reset]
                self.on('change:login_mode', self, function() {
                    var mode = self.get('login_mode') || 'default';
                    self.$('*[data-modes]').each(function() {
                        var modes = $(this).data('modes').split(/\s+/);
                        $(this).toggle(modes.indexOf(mode) > -1);
                    });
                    self.$('a.oe_login_otp:visible').toggle(self.twostep_enabled);
                });

                // to switch between the signup and regular login form
                self.$('a.oe_login_otp').click(function(ev) {
                    self.set('login_mode', 'login_otp');
                    return false;
                });

                self.$('a.oe_otp_back').click(function(ev) {
                    self.set('login_mode', 'default');
                    delete self.params.token;
                    return false;
                });

                var dbname = self.selected_db;

                // if there is an error message in params, show it then forget it
                if (self.params.error_message) {
                    self.show_error(self.params.error_message);
                    delete self.params.error_message;
                }

                if (dbname && self.params.login) {
                    self.$("form input[name=login]").val(self.params.login);
                }

                if (dbname) {
                    self.rpc("/auth_2step/get_config", {dbname: dbname}).then(function(result) {
                        self.twostep_enabled = result.otp;
                        if (!self.twostep_enabled || self.$("form input[name=login]").val()){
                            self.set('login_mode', 'default');
                        } else {
                            self.set('login_mode', 'login_otp');
                        }
                    });
                } else {
                    // TODO: support multiple database mode
                    self.set('login_mode', 'default');
                }
            });
        },


        get_params: function(){
            // signup user (or reset password)
            var db = this.$("form [name=db]").val();
            var otp_key = this.$("form input[name=otp_key]").val();
            var login = this.$("form input[name=login]").val();
            var password = this.$("form input[name=password]").val();
            if (!db) {
                this.do_warn(_t("Login"), _t("No database selected !"));
                return false;
            } else if (!otp_key) {
                this.do_warn(_t("Login"), _t("Please enter a OTP."));
                return false;
            } else if (!login) {
                this.do_warn(_t("Login"), _t("Please enter a username."));
                return false;
            }
            var params = {
                dbname : db,
                token: this.params.token || "",
                name: name,
                login: login,
                password: password,
                otp_key: otp_key,
            };
            return params;
        },

        get_params2: function(){
            // signup user (or reset password)
            var db = this.$("form [name=db]").val();
            var login = this.$("form input[name=login]").val();
            var password = this.$("form input[name=password]").val();
            if (!db) {
                this.do_warn(_t("Login"), _t("No database selected !"));
                return false;
            } else if (!login) {
                this.do_warn(_t("Login"), _t("Please enter a username."));
                return false;
            }
            var params = {
                dbname : db,
                token: this.params.token || "",
                name: name,
                login: login,
                password: password,
            };
            return params;
        },

        on_submit: function(ev) {
            if (ev) {
                ev.preventDefault();
            }
            var login_mode = this.get('login_mode');
            if (login_mode === 'login_otp') {
                var params = this.get_params();
                if (_.isEmpty(params)){
                    return false;
                }
                var self = this,
                    super_ = this._super;
                this.rpc('/auth_2step/validated_otp', params)
                    .done(function(result) {
                        if (result.error) {
                            self.show_error(result.error);
                        } else {
                            super_.apply(self, [ev]);
                        }
                    });
            } else {
                // regular login

                var params = this.get_params2();
                if (_.isEmpty(params)){
                    return false;
                }
                var self = this,
                    super_ = this._super;
                this.rpc('/auth_2step/send_otp', params)
                    .done(function(result) {
                        if (result.error) {
                            self.show_error(result.error);
                        }
                    });

                this.rpc('/auth_2step/show_opt', params)
                    .done(function(result) {
                        if (result == 1){
                            self.set('login_mode', 'login_otp');
                            return false;
                        } else {
                            super_.apply(self, [ev]);
                        }
                    });

            }
        },

    });
};
