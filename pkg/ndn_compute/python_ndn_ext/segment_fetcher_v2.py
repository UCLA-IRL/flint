import asyncio
from ndn.appv2 import NDNApp, Validator
from ndn.encoding import Name, Component
from ndn.types import InterestNack, MetaInfo, InterestTimeout


async def fetch_segments(app: NDNApp, name: Name, validator: Validator,
                         must_be_fresh: bool = False, lifetime: int = 6000,
                         initial_backoff: list[int] = [0, 0.5, 0.5, 1, 2, 3, 4, 5, 10, 20, 30]):
    """
    Syntactic sugar to fetch segmented data.

    This method does not assume the first segment is immediately available, instead it will try len(initial_backoff)
    times with initial_backoff[i] seconds of wait before the ith try.

    :param app: NDNApp object to send interests from
    :param name: Name of the data (to which a segment component will be added at the end)
    :param validator: Data validator for all returned data
    :param must_be_fresh: Passed to app.express
    :param lifetime: Passed to app.express
    :param initial_backoff: Backoff pattern (in seconds) to wait for the first segment to become available.
    """
    first_segment_available = False
    for sleep_time in initial_backoff:
        if first_segment_available:
            raise Exception(f"Data {Name.to_str(name)} became unavailable midway through fetching")

        await asyncio.sleep(sleep_time)
        try:
            current_segment = 0
            final_segment_uninitialized = True
            final_segment = -1

            while final_segment_uninitialized or current_segment <= final_segment:
                request_name = name + [Component.from_segment(current_segment)]
                data_name, content, context = await app.express(
                    request_name,
                    validator,
                    must_be_fresh=must_be_fresh,
                    can_be_prefix=True,  # allow for NACKs
                    lifetime=lifetime)

                if Name.to_str(data_name) != Name.to_str(request_name):
                    raise Exception(f"Requested segment {Name.to_str(request_name)} got back non-matching name " +
                                    f"{Name.to_str(data_name)}")

                if final_segment_uninitialized:
                    final_segment_uninitialized = False
                    if 'meta_info' not in context or not isinstance(context['meta_info'], MetaInfo):
                        raise Exception(f"MetaInfo malformed or missing from reply: {Name.to_str(data_name)}")

                    meta_info: MetaInfo = context['meta_info']
                    if not meta_info.final_block_id:
                        raise Exception(f"Segmented data must have final block ID: {Name.to_str(data_name)}")

                    final_segment = Component.to_number(meta_info.final_block_id)
                    if final_segment < 0:
                        raise Exception(f"Final block ID invalid for data: {Name.to_str(data_name)}")

                current_segment += 1

                first_segment_available = True

                yield content

            return
        except InterestNack as e:
            # A NACK is received
            print(f'fetch_segments: Nacked with reason={e.reason}, continue to wait', flush=True)
            continue

    raise Exception("fetch_segments failed, exhausted attempts to fetch the first segment")
