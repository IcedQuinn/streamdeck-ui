from fractions import Fraction
from typing import Dict, List, Tuple

from PIL.Image import Image

from streamdeck_ui.display.filter import Filter


class Pipeline:
    def __init__(self) -> None:
        self.filters: List[Tuple[Filter, Image]] = []
        self.first_run = True
        self.output_cache: Dict[int, Image] = {}

    def add(self, filter: Filter) -> None:
        self.filters.append((filter, None))
        self.first_run = True

    def execute(self, time: Fraction) -> Tuple[Image, int]:
        """
        Executes all the filter in the pipeline and returns the final image, or None if the pipeline did not yield any changes.
        """

        image: Image
        is_modified = False
        pipeline_hash = 0

        for i, (current_filter, cached) in enumerate(self.filters):

            (image, hashcode) = current_filter.transform(lambda: image.copy(), lambda output_hash: self.output_cache.get(hash((output_hash, pipeline_hash)), None), is_modified | self.first_run, time)

            pipeline_hash = hash((hashcode, pipeline_hash))

            if not image:
                # Filter indicated that it did NOT change anything, pull up the last
                # cached value for the next step in the pipeline
                image = cached
            else:
                # The filter changed the image, cache it for future use
                # Update tuple with cached image
                self.filters[i] = (current_filter, image)
                is_modified = True

            # Store this image with pipeline hash if we haven't seen it.
            if pipeline_hash not in self.output_cache:
                self.output_cache[pipeline_hash] = image

        if self.first_run:
            # Force an update the first time the pipeline runs
            is_modified = True
            self.first_run = False

        return (image if is_modified else None, pipeline_hash)

    def last_result(self) -> Image:
        """
        Returns the last known output of the pipeline
        """
        return self.filters[-1][1]
