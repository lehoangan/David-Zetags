from openerp.service import security
import openerp.pooler as pooler

def login(db, login, password):
    pool = pooler.get_pool(db)
    user_obj = pool.get('res.users')
    res = user_obj.login(db, login, password)
    print '==============', res
    return res

security.login=login
# security.check=check
# security.access=access