from random import choice, random, randrange, uniform
import pytest

from htsohm.material_files import random_number_density
from htsohm.db.__init__ import Structure

@pytest.fixture
def LCs():
    structure = Structure()
    structure.lattice_constant_a = 1
    structure.lattice_constant_b = 1
    structure.lattice_constant_c = 1
    return structure

def test_number_density_bounds():
    assert random_number_density((100000, 100000), LCs()) == 100000

def test_two_site_constraint():
    assert random_number_density((1, 2), LCs()) == 2

