# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Components to read HESSIO data.  

This requires the hessio python library to be installed
"""

from .containers import RawData, RawCameraData

import logging
logger = logging.getLogger(__name__)

try:
    import hessio
except ImportError as err:
    logger.fatal("the `hessio` python module is required to access MC data: {}"
                 .format(err))
    raise err

__all__ = [
    'hessio_event_source',
]


def hessio_event_source(url, max_events=None):
    """A generator that streams data from an EventIO/HESSIO MC data file
    (e.g. a standard CTA data file.)

    Parameters
    ----------
    url : str
        path to file to open
    max_events : int, optional
        maximum number of events to read
    """

    ret = hessio.file_open(url)

    if ret is not 0:
        raise RuntimeError("hessio_event_source failed to open '{}'"
                           .format(url))

    counter = 0
    eventstream = hessio.move_to_next_event()
    event = RawData()
    event.meta.add_item('hessio__input', url)
    event.meta.add_item('hessio__max_events', max_events)

    for run_id, event_id in eventstream:

        event.run_id = run_id
        event.event_id = event_id
        event.tels_with_data = hessio.get_teldata_list()

        # this should be done in a nicer way to not re-allocate
        # the data each time

        for tel_id in event.tels_with_data:

            # fill pixel position dictionary, if not already done:
            if tel_id not in event.pixel_pos:
                event.pixel_pos[tel_id] = hessio.get_pixel_position(tel_id)

            nchans = hessio.get_num_channel(tel_id)
            event.tel_data[tel_id] = RawCameraData(tel_id)
            event.tel_data[tel_id].num_channels = nchans

            # load the data per telescope/chan
            for chan in range(nchans):
                event.tel_data[tel_id].adc_samples[chan] \
                    = hessio.get_adc_sample(channel=chan,
                                            telescopeId=tel_id)
                event.tel_data[tel_id].adc_sums[chan] \
                    = hessio.get_adc_sum(channel=chan,
                                         telescopeId=tel_id)
        yield event
        counter += 1

        if counter > max_events:
            return