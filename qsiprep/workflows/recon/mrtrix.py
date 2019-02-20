import json
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as niu
from nipype.utils.filemanip import copyfile, split_filename

import logging
import os
import os.path as op
from qsiprep.interfaces.bids import QsiprepOutput, ReconDerivativesDataSink
from qsiprep.interfaces.utils import GetConnectivityAtlases
from qsiprep.interfaces.connectivity import Controllability
from qsiprep.interfaces.gradients import RemoveDuplicates
from qsiprep.interfaces.mrtrix import ResponseSD, EstimateFOD, MRTrixIngress

LOGGER = logging.getLogger('nipype.interface')
qsiprep_output_names = QsiprepOutput().output_spec.class_editable_traits()
default_connections = [(trait, trait) for trait in qsiprep_output_names]
default_input_set = set(qsiprep_output_names)


def init_mrtrix_vanilla_csd_recon_workflow(name="mrtrix_recon", output_suffix="", params={}):
    inputnode = pe.Node(niu.IdentityInterface(fields=qsiprep_output_names),
                        name="inputnode")
    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=['mif_file']),
        name="outputnode")

    workflow = pe.Workflow(name=name)
    create_mif = pe.Node(MRTrixIngress(), name='create_mif')
    estimate_response = pe.Node(ResponseSD(**params['response']), 'estimate_response')
    estimate_fod = pe.Node(EstimateFOD(gm_txt="", csf_txt="", gm_odf="", csf_odf="",
                                       **params['fod']), 'estimate_fod')

    workflow.connect([
        (inputnode, create_mif, [('dwi_file', 'dwi_file'),
                                 ('bval_file', 'bval_file'),
                                 ('bvec_file', 'bvec_file'),
                                 ('b_file', 'b_file')]),
        (create_mif, estimate_response, [('mif_file', 'in_file')]),
        (inputnode, estimate_response, [('mask_file', 'in_mask')]),
        (create_mif, estimate_fod, [('mif_file', 'in_file')]),
        (estimate_response, estimate_fod, [('wm_file', 'wm_txt')]),
        (estimate_fod, outputnode, [('wm_odf', 'mif_file')])

    ])
    return workflow
