from lab.reports import Attribute

def get():
    cpdbs_num_pdbs = Attribute('cpdbs_num_pdbs', absolute=False, min_wins=True)
    cpdbs_num_pdb_lookups = Attribute('cpdbs_num_pdb_lookups', absolute=False, min_wins=True)
    cpdbs_estimated_memory_usage = Attribute('cpdbs_estimated_memory_usage', absolute=False, min_wins=True)
    cpdbs_size = Attribute('cpdbs_size', absolute=False, min_wins=True)

    attributes = [
        cpdbs_num_pdbs,
        cpdbs_num_pdb_lookups,
        cpdbs_estimated_memory_usage,
        cpdbs_size,
    ]

    return attributes
