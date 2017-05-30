# from htsohm.db.runDB_declarative import *

# standard library imports
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import yaml

# Init the database
with open(os.path.join('settings', 'database.yaml'), 'r') as yaml_file:
    dbconfig = yaml.load(yaml_file)
connection_string = dbconfig['connection_string']
if 'sqlite' in connection_string:
    print(
        'WARNING: attempting to use SQLite database! Okay for local debugging\n' +
        'but will not work with multiple workers, due to lack of locking features.'
    )
engine = create_engine(connection_string)
session = sessionmaker(bind=engine)()

# Import all models
from htsohm.db.base import Base
from htsohm.db.material import Material
from htsohm.db.mutation_strength import MutationStrength
from htsohm.db.structure import Structure
from htsohm.db.atom_sites import AtomSites
from htsohm.db.lennard_jones import LennardJones

# Create tables in the engine, if they don't exist already.
Base.metadata.create_all(engine)
Base.metadata.bind = engine
