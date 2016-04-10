from openerp.osv import fields, osv
from random import choice
import string

class ResUSers(osv.osv):
    _inherit = 'res.users'
    _columns = {
        'otp_key': fields.char('OTP key', size=128, help="This is the OTP secret (private) key"),
        '2_step':  fields.boolean(string='2 Step Login'),
    }

    def _check_otp(self, cr, uid, values, token=None, context=None):
        login = values.get('login')
        otp = values.get('otp_key')
        user_ids = self.search(cr, uid, [('login', '=', login)])
        if not user_ids:
            raise osv.except_osv('Syntax Error !', 'User Error')

        otp_key = self.browse(cr, uid, user_ids[0]).otp_key
        if otp != otp_key:
            raise osv.except_osv('Syntax Error !', 'User Error')

        return (cr.dbname, values.get('login'), values.get('password'))

    def _check_show_otp(self, cr, uid, values, token=None, context=None):
        login = values.get('login')
        user_ids = self.search(cr, uid, [('login', '=', login)])
        if not user_ids:
            raise osv.except_osv('Syntax Error !', 'User Error')

        return self.browse(cr, uid, user_ids[0])['2_step'] and 1 or 0

    def _send_otp(self, cr, uid, values, token=None, context=None):
        def GenPasswd2(length=8, chars=string.letters + string.digits):
            return ''.join([choice(chars) for i in range(length)])

        otp = GenPasswd2(4,string.digits) + GenPasswd2(3,string.ascii_letters)
        login = values.get('login')
        user_ids = self.search(cr, uid, [('login', '=', login)])
        self.write(cr, uid, user_ids, {'otp_key': otp})
        self.send_email(cr, uid, user_ids, context)
        return

    def send_email(self, cr, uid, ids, context=None):
        """ create signup token for each user, and send their signup url by email """

        if not context:
            context = {}

        template = self.pool.get('ir.model.data').get_object(cr, uid, 'auth_2step', 'otp_login_email')
        mail_obj = self.pool.get('mail.mail')
        assert template._name == 'email.template'
        for user in self.browse(cr, uid, ids, context):
            if not user.email:
                raise osv.except_osv(_("Cannot send email: user has no email address."), user.name)
            mail_id = self.pool.get('email.template').send_mail(cr, uid, template.id, user.id, True, context=context)
            mail_state = mail_obj.read(cr, uid, mail_id, ['state'], context=context)
            if mail_state and mail_state['state'] == 'exception':
                raise osv.except_osv(_("Cannot send email: no outgoing email server configured.\nYou can configure it under Settings/General Settings."), user.name)
            else:
                return True




ResUSers()
