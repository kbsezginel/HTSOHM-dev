
import sys
import uuid

from sqlalchemy import Column, ForeignKey, Integer, String, Float, Boolean
from sqlalchemy.sql import text
from sqlalchemy.orm import relationship

from htsohm import config
from htsohm.db import Base, session, engine

class AtomSites(Base):
    """    """
    __tablename__ = 'atom_sites'

    id = Column(Integer, primary_key=True)
    chemical_id = Column(String(10))
    x_frac = Column(Float)
    y_frac = Column(Float)
    z_frac = Column(Float)
    charge = Column(Float)

    # relationship with 'structures'
    structure_id = Column(Integer, ForeignKey('structure.id'))
#    structure = relationship("Structure", back_populates="atom_sites")

#    def __init__(self, chemical_id=None, x_frac=None, y_frac=None, z_frac=None, charge=None):
#        """   """
#        self.chemical_id = chemical_id
#        self.x_frac = x_frac
#        self.y_frac = y_frac
#        self.z_frac = z_frac
#        self.charge = charge
