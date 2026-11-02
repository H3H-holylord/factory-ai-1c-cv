from dataclasses import dataclass, field
import math
from typing import List


@dataclass(frozen=True)
class BoundingBox:
    x1: int
    y1: int
    x2: int
    y2: int
    label: str = "part"
    confidence: float = 0.96

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0)

    def contains_point(self, x: float, y: float) -> bool:
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2


@dataclass
class TrackedItem:
    track_id: int
    bbox: BoundingBox
    prev_center: tuple[float, float]
    frames_seen: int = 1
    counted: bool = False


@dataclass(frozen=True)
class CounterState:
    total_count: int
    tracked_items: List[TrackedItem] = field(default_factory=list)


def _match_tracks(
    existing: List[TrackedItem],
    detections: List[BoundingBox],
    max_distance: float,
    next_id_start: int,
) -> tuple[List[TrackedItem], int]:
    unmatched_existing = list(existing)
    updated: List[TrackedItem] = []
    next_id = next_id_start

    for det in detections:
        cx, cy = det.center
        best_item = None
        best_dist = max_distance

        for item in unmatched_existing:
            ix, iy = item.bbox.center
            dist = math.hypot(cx - ix, cy - iy)
            if dist <= best_dist:
                best_dist = dist
                best_item = item

        if best_item is not None:
            unmatched_existing.remove(best_item)
            updated.append(
                TrackedItem(
                    track_id=best_item.track_id,
                    bbox=det,
                    prev_center=best_item.bbox.center,
                    frames_seen=best_item.frames_seen + 1,
                    counted=best_item.counted,
                )
            )
        else:
            updated.append(
                TrackedItem(
                    track_id=next_id,
                    bbox=det,
                    prev_center=det.center,
                    frames_seen=1,
                    counted=False,
                )
            )
            next_id += 1

    return updated, next_id


class ConveyorCounter:
    """Counts casting parts (1-3 in a row) crossing a virtual line x = line_x."""

    def __init__(self, line_x: int, max_match_distance: float = 80.0):
        self.line_x = line_x
        self.max_match_distance = max_match_distance
        self.total_count = 0
        self._tracks: List[TrackedItem] = []
        self._next_id = 1

    def update(self, detections: List[BoundingBox]) -> CounterState:
        self._tracks, self._next_id = _match_tracks(
            self._tracks, detections, self.max_match_distance, self._next_id
        )

        for item in self._tracks:
            prev_x, _ = item.prev_center
            curr_x, _ = item.bbox.center
            if not item.counted and prev_x < self.line_x <= curr_x:
                item.counted = True
                self.total_count += 1

        return CounterState(total_count=self.total_count, tracked_items=list(self._tracks))


class WeldingZoneCounter:
    """Counts welded parts placed inside an ROI zone after confirm_frames debounce."""

    def __init__(
        self,
        roi: BoundingBox,
        confirm_frames: int = 5,
        max_match_distance: float = 60.0,
    ):
        self.roi = roi
        self.confirm_frames = confirm_frames
        self.max_match_distance = max_match_distance
        self.total_count = 0
        self._tracks: List[TrackedItem] = []
        self._next_id = 1

    def update(self, detections: List[BoundingBox]) -> CounterState:
        inside = [d for d in detections if self.roi.contains_point(*d.center)]
        self._tracks, self._next_id = _match_tracks(
            self._tracks, inside, self.max_match_distance, self._next_id
        )

        for item in self._tracks:
            if not item.counted and item.frames_seen >= self.confirm_frames:
                item.counted = True
                self.total_count += 1

        return CounterState(total_count=self.total_count, tracked_items=list(self._tracks))
