"""Order native Wan model loading after the preceding stage has released weights.

These nodes reuse ComfyUI's UNETLoader without changing weights, conditioning,
latents, precision or sampling. The extra inputs enforce execution dependencies.
"""
import gc
import json
import logging
import os

import psutil

import comfy.model_management as memory
import comfy.system_memory
from nodes import UNETLoader


def release_previous_stage(label):
    process = psutil.Process(os.getpid())
    before = {'available_ram_bytes': comfy.system_memory.virtual_memory_available(),
              'process_rss_bytes': process.memory_info().rss}
    memory.unload_all_models()
    gc.collect()
    memory.soft_empty_cache()
    after = {'available_ram_bytes': comfy.system_memory.virtual_memory_available(),
             'process_rss_bytes': process.memory_info().rss}
    logging.info('OpenMontage stage release: %s', json.dumps({'next_stage': label, 'before': before, 'after': after}))


class TextThenUNETLoader:
    RETURN_TYPES = ('MODEL',)
    FUNCTION = 'load_staged'
    CATEGORY = 'OpenMontage/memory'

    @classmethod
    def INPUT_TYPES(cls):
        required = dict(UNETLoader.INPUT_TYPES()['required'])
        required.update(positive=('CONDITIONING',), negative=('CONDITIONING',))
        return {'required': required}

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float('nan')

    def load_staged(self, unet_name, weight_dtype, positive, negative):
        release_previous_stage('high-noise model')
        return UNETLoader().load_unet(unet_name, weight_dtype)


class LatentThenUNETLoader:
    RETURN_TYPES = ('MODEL',)
    FUNCTION = 'load_staged'
    CATEGORY = 'OpenMontage/memory'

    @classmethod
    def INPUT_TYPES(cls):
        required = dict(UNETLoader.INPUT_TYPES()['required'])
        required['samples'] = ('LATENT',)
        return {'required': required}

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float('nan')

    def load_staged(self, unet_name, weight_dtype, samples):
        release_previous_stage('low-noise model')
        return UNETLoader().load_unet(unet_name, weight_dtype)


NODE_CLASS_MAPPINGS = {
    'OpenMontageTextThenUNETLoader': TextThenUNETLoader,
    'OpenMontageLatentThenUNETLoader': LatentThenUNETLoader,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    'OpenMontageTextThenUNETLoader': 'Release text encoder, then load Wan',
    'OpenMontageLatentThenUNETLoader': 'Release previous Wan, then load next',
}
