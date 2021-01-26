from . import default


def get_enabled_transformers(transformers_settings):
    transformers = []
    if transformers_settings['reduce-request-in-ts-precision']:
        transformers.append(default.reduce_request_in_ts_precision)
    if transformers_settings['force-durations-to-integer-range']:
        transformers.append(default.force_durations_to_integer_range)

    return transformers

