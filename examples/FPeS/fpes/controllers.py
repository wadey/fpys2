from turbogears import controllers, expose, flash
from model import *
from turbogears import config
from turbogears import identity, redirect
from cherrypy import request, response
from cherrypy import session as httpsession
# from fpes import json
import logging
import fpys
# identity creation
import base64, random, uuid

log = logging.getLogger("fpes.controllers")

fpys_client = fpys.FlexiblePaymentClient(config.get("aws_access_key_id"),
                                         config.get("secret_access_key"))

class Root(controllers.RootController):
    @identity.require(identity.not_anonymous())
    @expose(template="fpes.templates.index")
    def index(self):
        return dict(works=Work.query().all())

    @expose()
    def add(self, id, **kw):
        if not httpsession.has_key('cart'):
            httpsession['cart'] = []
        httpsession['cart'].append(int(id))
        print httpsession['cart']
        raise redirect("/cart")

    @expose()
    def remove(self, id, **kw):
        id = int(id)
        if httpsession.has_key('cart'):
            for w in httpsession['cart']:
                if w == id:
                    httpsession['cart'].remove(w)
            
        raise redirect("/cart")

    @expose()
    def remove_all(self):
        httpsession['cart'] = []
        raise redirect("/cart")

    @expose(template="fpes.templates.cart")
    def cart(self):
        works = []
        if httpsession.has_key('cart'):
            for w in httpsession['cart']:
                works.append(Work.query().filter(Work.c.id==w).first())
        return {'works': works}

    @expose()
    def purchase(self):
        if not httpsession.has_key("cart"):
            redirect("/cart")

        session.begin()
        print "in transaction"
        invoice = Invoice()
        print invoice.invoice_date
        line_items = []
        for item in httpsession['cart']:
            li = LineItem()
            li.work_id = item
            li.quantity = 1
            li.unit_price = 1
            line_items.append(li)
        invoice.line_items = line_items

        session.commit()
        session.flush()

        host = request.headers['Host']
        if request.headers.has_key('X-Forwarded-Host'):
            host = request.headers['X-Forwarded-Host']

        url = fpys_client.getPipelineUrl(invoice.caller_reference,
                                         "Image Download",
                                         str(invoice.total),
                                         "http://%s/capture/%d" % (host, invoice.id))
        raise redirect(url)

    @expose()
    def capture(self, invoice_id, **params):
        print params
        path = "/capture/%s?" % invoice_id
        # is amazon not url encoding the signature? 
        sig = params['awsSignature'].replace(" ", "+")
        if not fpys_client.validate_pipeline_signature(sig, path, params):
            return("invalid signature")

        if params['status'] in ['SA', 'SB', 'SC']:
            invoice = Invoice.query().filter(Invoice.c.id == int(invoice_id)).first()
            invoice.sender_token = params['tokenID']
            invoice.install_recipient_token(fpys_client)
            response = invoice.pay(fpys_client, config.get("default_caller_token"))

            import xml.etree.ElementTree as ET
            print response.transaction.status
            print response.transaction.transactionId
            
            for li in invoice.line_items:
                works_users_table.insert(dict(work_id=li.work_id,
                                              user_id=identity.current.user.user_id)).execute()
            redirect("/mine")
        else:
            return("The payment didn't succeed")

    @expose(template="fpes.templates.mine")
    def mine(self):
        works = work_table.join(works_users_table).select(works_users_table.c.user_id==identity.current.user.user_id).execute()
        return {'works': works}
    
    @expose(template="fpes.templates.login")
    def login(self, forward_url=None, previous_url=None, *args, **kw):
        print "logging in"
        if not identity.current.anonymous \
            and identity.was_login_attempted() \
            and not identity.get_identity_errors():
            raise redirect(forward_url)

        session.begin()
        password = base64.encodestring(str(random.getrandbits(64))).strip()
        username = uuid.uuid1().hex
        user = User(user_name=username, 
                    display_name='Guest User', 
                    password=identity.encrypt_password(password))
        session.commit()
        session.flush()

        identity.current_provider.validate_identity(username,
                                                    password,
                                                    identity.current.visit_key)
        raise redirect(request.path)

    @expose()
    def logout(self):
        identity.current.logout()
        raise redirect("/")

    @expose()
    def dump_data(self, **args):
        print args
        return args
