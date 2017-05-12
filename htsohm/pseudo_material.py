import os

import yaml

import htsohm
from htsohm.files import load_config_file
from htsohm.pseudo_simulation import pseudo_void_fraction
from htsohm.pseudo_simulation import pseudo_surface_area
from htsohm.pseudo_simulation import pseudo_gas_adsorption

class PseudoMaterial:
    """Class for storing pseudomaterial structural data.

    Attributes:
        uuid (str) : Version 4 UUID used to identify pseudomaterial record in
            `materials` database.
        run_id (str) : identification string distinguishing runs.
        lattice_constants (dict) : crystal lattice parameters:
                {
                    'a' : float,
                    'b' : float,
                    'c' : float
                }
        atom_types (list : dict) : Lennard-Jones parameters and partial charge:
                [
                    {
                        "chemical-id"  : str,
                        "charge"       : float,
                        "epsilon"      : float,
                        "sigma"        : float
                    }
                ]
        atom_sites (list : dict) : atom-site locations as fractions:
                [
                    {
                        "chemical-id"  : str,
                        "x-frac"       : float,
                        "y-frac"       : float,
                        "z-frac"       : float
                    }
                ]
    """

    def __init__(self, uuid):
        """Instantiates PseudoMaterial object with real uuid and null values for
        all other attributes.
        
        Args:
            uuid (str) : Version 4 UUID identifying pseudomaterial record in
                `materials` database.

        Returns:
            None

        """
        self.uuid = uuid
        self.run_id = None
        self.lattice_constants = {
                "a" : None,
                "b" : None, 
                "c" : None
                }
        self.atom_types= [
                {
                    "chemical-id"  : None,
                    "charge"       : None,
                    "epsilon"      : None,
                    "sigma"        : None
                    }
                ]
        self.atom_sites = [
                {
                    "chemical-id"  : None,
                    "x-frac"       : None,
                    "y-frac"       : None,
                    "z-frac"       : None
                    }
                ]

    def __repr__(self):
        return ('{0.__class__.__name__!s}('
                '{0.uuid!r}, '
                '{0.run_id!r}, '
                '{0.lattice_constants!r}, '
                '{0.atom_types!r}, '
                '{0.atom_sites!r})').format(self)

    def dump(self):
        htsohm_dir = os.path.dirname(os.path.dirname(htsohm.__file__))
        pseudo_materials_dir = os.path.join(
                htsohm_dir, 
                self.run_id, 
                'pseudo_materials')
        if not os.path.exists(pseudo_materials_dir):
            os.makedirs(pseudo_materials_dir, exist_ok=True)
        pseudo_material_file = os.path.join(
                pseudo_materials_dir,
                '{0}.yaml'.format(self.uuid))
        with open(pseudo_material_file, "w") as dump_file:
            yaml.dump(self, dump_file)

    def volume(self):
        return (
                self.lattice_constants["a"] *
                self.lattice_constants["b"] *
                self.lattice_constants["c"]
            )

    def number_density(self):
        return len(self.atom_sites) / self.volume()

    def average_sigma(self):
        sigmas = []
        for atom_type in self.atom_types:
            sigmas.append(atom_type['sigma'])
        return sum(sigmas) / max(len(sigmas), 1)

    def average_epsilon(self):
        epsilons = []
        for atom_type in self.atom_types:
            epsilons.append(atom_type['epsilon'])
        return sum(epsilons) / max(len(epsilons), 1)

    def artificial_void_fraction(self):
        htsohm_dir = os.path.dirname(os.path.dirname(htsohm.__file__))
        config_file = os.path.join(htsohm_dir, self.run_id, 'config.yaml')
        config = load_config_file(config_file)

        return pseudo_void_fraction(
                config, self.number_density(), self.average_sigma())

    def artificial_surface_area(self):
        return pseudo_surface_area(
                self.artificial_void_fraction(), self.average_sigma())

    def artificial_gas_adsorption(self):
        htsohm_dir = os.path.dirname(os.path.dirname(htsohm.__file__))
        config_file = os.path.join(htsohm_dir, self.run_id, 'config.yaml')
        config = load_config_file(config_file)
        
        return pseudo_gas_adsorption(
                config, self.artificial_void_fraction(),
                self.artificial_surface_area(), self.average_epsilon())
