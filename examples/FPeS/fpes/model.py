from datetime import datetime
from sqlalchemy import *
from sqlalchemy.orm import relation
from turbogears.database import metadata, session
from turbogears import identity
from sqlalchemy.ext.assignmapper import assign_mapper
import uuid

import logging
log = logging.getLogger("fpysfpes.model")


def assign(*args, **kw):
    """Map tables to objects with knowledge about the session context."""
    return assign_mapper(session.context, *args, **kw)

invoice_table = Table('invoice', metadata,
                      Column('id', Integer, primary_key=True),
                      Column('user_id', Integer, ForeignKey('tg_user.user_id')),
                      Column('invoice_date', DateTime, default=datetime.now),
                      Column('payment_info', String),
                      Column('recipient_token', String),
                      Column('sender_token', String))

line_item_table = Table('line_item', metadata,
                        Column('id', Integer, primary_key=True),
                        Column('work_id', Integer, ForeignKey('work.id')),
                        Column('invoice_id', Integer, ForeignKey('invoice.id')),
                        Column('quantity', Integer, default=1),
                        Column('unit_price', Float, default=1.00))
                            
work_table = Table('work', metadata,
                    Column('id', Integer, primary_key=True),
                    Column('title', String),
                    Column('file_path', String),
                    Column('description', String),
                    Column('purchases', Integer, default=0))

works_users_table = Table('works_users', metadata,
                          Column('work_id', Integer, ForeignKey('work.id')),
                          Column('user_id', Integer, ForeignKey('tg_user.user_id')))

class Invoice(object):
    def get_caller_reference(self):
        return "fpes.achievewith.us_%d_%s" % (self.id, self.invoice_date.strftime("%Y%m%d%H%M%S"))
    caller_reference = property(get_caller_reference, None)

    def get_payment_reason(self):
        return 'FPeS Invoice #%d' % self.id
    payment_reason = property(get_payment_reason, None)

    def get_total(self):
        total = 0.0
        for l in self.line_items:
            total += (l.unit_price * l.quantity)
        return total

    total = property(get_total, None)

    def install_recipient_token(self, fps_client):
        pi = """MyRole == 'Recipient' orSay 'Role does not match';
TransactionAmount == 'USD %f';
SenderToken == '%s';
""" % (self.total, self.sender_token)

        response = fps_client.installPaymentInstruction(payment_instruction=pi,
                                                        caller_reference=self.caller_reference + "_recipient",
                                                        token_type='SingleUse',
                                                        payment_reason=self.payment_reason,
                                                        token_friendly_name=self.caller_reference + "_recipient")
        self.recipient_token = response.tokenId
        

    def pay(self, fps_client, caller_token):
        return fps_client.pay(caller_token,
                              self.sender_token,
                              self.recipient_token,
                              self.total,
                              self.payment_reason)
    
class LineItem(object):
    pass

class Work(object):
    def __init__(self, dict=None):
        if dict is not None:
            for k, v in dict.items():
                setattr(self, k, v)

session.mapper(Invoice, invoice_table,
       properties=dict(line_items = relation(LineItem, backref='invoice')))
session.mapper(LineItem, line_item_table)
session.mapper(Work, work_table)


# The identity schema.
visits_table = Table('visit', metadata,
    Column('visit_key', String(40), primary_key=True),
    Column('created', DateTime, nullable=False, default=datetime.now),
    Column('expiry', DateTime)
)

visit_identity_table = Table('visit_identity', metadata,
    Column('visit_key', String(40), primary_key=True),
    Column('user_id', Integer, ForeignKey('tg_user.user_id'), index=True)
)

groups_table = Table('tg_group', metadata,
    Column('group_id', Integer, primary_key=True),
    Column('group_name', Unicode(16), unique=True),
    Column('display_name', Unicode(255)),
    Column('created', DateTime, default=datetime.now)
)

users_table = Table('tg_user', metadata,
    Column('user_id', Integer, primary_key=True),
    Column('user_name', Unicode(128), unique=True),
    Column('display_name', Unicode(255)),
    Column('password', Unicode(40)),
    Column('created', DateTime, default=datetime.now)
)

permissions_table = Table('permission', metadata,
    Column('permission_id', Integer, primary_key=True),
    Column('permission_name', Unicode(16), unique=True),
    Column('description', Unicode(255))
)

user_group_table = Table('user_group', metadata,
    Column('user_id', Integer, ForeignKey('tg_user.user_id',
        onupdate="CASCADE", ondelete="CASCADE")),
    Column('group_id', Integer, ForeignKey('tg_group.group_id',
        onupdate="CASCADE", ondelete="CASCADE"))
)

group_permission_table = Table('group_permission', metadata,
    Column('group_id', Integer, ForeignKey('tg_group.group_id',
        onupdate="CASCADE", ondelete="CASCADE")),
    Column('permission_id', Integer, ForeignKey('permission.permission_id',
        onupdate="CASCADE", ondelete="CASCADE"))
)

# identity model
class Visit(object):
    """
    A visit to your site
    """
    def lookup_visit(cls, visit_key):
        return session.query(Visit).get(visit_key)
    lookup_visit = classmethod(lookup_visit)

class VisitIdentity(object):
    """
    A Visit that is link to a User object
    """
    pass

class Group(object):
    """
    An ultra-simple group definition.
    """
    pass

class User(object):
    """
    Reasonably basic User definition. Probably would want additional
    attributes.
    """
    def permissions(self):
        perms = set()
        for g in self.groups:
            perms = perms | set(g.permissions)
        return perms
    permissions = property(permissions)

    def by_email_address(klass, email):
        """
        A class method that can be used to search users
        based on their email addresses since it is unique.
        """
        return session.query(klass).filter_by(email_address=email).first()

    by_email_address = classmethod(by_email_address)

    def by_user_name(klass, username):
        """
        A class method that permits to search users
        based on their user_name attribute.
        """
        return session.query(klass).filter_by(user_name=username).first()

    by_user_name = classmethod(by_user_name)

    def _set_password(self, password):
        """
        encrypts password on the fly using the encryption
        algo defined in the configuration
        """
        self._password = identity.encrypt_password(password)

    def _get_password(self):
        """
        returns password
        """
        return self._password

    password = property(_get_password, _set_password)

class Permission(object):
    """
    A relationship that determines what each Group can do
    """
    pass

session.mapper(Visit, visits_table)
session.mapper(VisitIdentity, visit_identity_table,
          properties=dict(users=relation(User, backref='visit_identity')))
session.mapper(User, users_table,
       properties=dict())
session.mapper(Group, groups_table,
          properties=dict(users=relation(User, secondary=user_group_table, backref='groups')))
session.mapper(Permission, permissions_table,
          properties=dict(groups=relation(Group, secondary=group_permission_table, backref='permissions')))

def init():
    if(len(Work.query().all()) > 0):
        return
    
    log.info("initializing data")

    works = [
    dict(title="Mountain Stream",
         file_path="mountain_stream",
         description="Taken in Colorado during the summer of 1999.",
         purchases=0,
         id=0),
    dict(title="Graffiti",
         file_path="graffiti",
         description="SpongeBob and Patrick in St. Joseph, Missouri.",
         purchases=0,
         id=1),
    dict(title="Lenexa Conference Center",
         file_path="lenexa_conference_center",
         description="Taken to scout out a wedding reception location.",
         purchases=0,
         id=2),
    dict(title="Glass",
         file_path="glass",
         description="Somewhere in California",
         purchases=0,
         id=3),    
    ]

    session.begin()
    for w in works:
        work = Work(dict=w)

    session.commit()
