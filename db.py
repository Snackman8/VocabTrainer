"""
    Create Record
    ==================================================
    session = Session()
    user = User(display_name='a', auth_username='b', auth_method='c')
    session.add(user)
    session.commit()

    Retrieve Record
    ==================================================
    session = Session()
    users = session.query(User).filter(User.auth_method == 'c')

    Update Record
    ==================================================
    session = Session()
    users = session.query(User).filter(User.auth_method == 'c')
    users.update({'display_name': 'xxx'})
    session.commit()

    Delete Record
    ==================================================
    session = Session()
    users = session.query(User).filter(User.auth_method == 'c')
    users.delete()
    session.commit()
"""

# --------------------------------------------------
#    Imports
# --------------------------------------------------
import os
from sqlalchemy import create_engine, Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# --------------------------------------------------
#    Globals
# --------------------------------------------------
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'db')
db_path = os.path.join(db_path, 'VocabTrainer.db')
if not os.path.exists(db_path):
    os.makedirs(db_path)
engine = create_engine("sqlite:///" + db_path)
Base = declarative_base()
Session = sessionmaker(bind = engine)


# --------------------------------------------------
#    ORM Classes
# --------------------------------------------------
class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    display_name = Column(String)
    auth_username = Column(String)
    auth_method = Column(String)

    def __repr__(self):
        return '<User(' + ','.join([f"""{x}={getattr(self, x)}""" for x in ['user_id', 'display_name', 'auth_username', 'auth_method']]) + ')>'



class UserProps(Base):
    __tablename__ = "user_props"
    user_prop_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    key = Column(String)
    value = Column(String)

    def __repr__(self):
        return '<User(' + ','.join([f"""{x}={getattr(self, x)}""" for x in ['user_prop_id', 'user_id', 'key', 'value']]) + ')>'


# create tables
Base.metadata.create_all(engine)
