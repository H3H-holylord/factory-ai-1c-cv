import pytest
from src.cv_counter import BoundingBox, ConveyorCounter, WeldingZoneCounter


def test_conveyor_counts_three_parts_in_a_row_crossing_line_once():
    # Line at x = 300. Three parts in a vertical row move from x=250 to x=350.
    counter = ConveyorCounter(line_x=300, max_match_distance=80.0)

    # Frame 1: before line (center x = 260)
    f1 = [
        BoundingBox(x1=240, y1=100, x2=280, y2=140, label="casting"),
        BoundingBox(x1=240, y1=220, x2=280, y2=260, label="casting"),
        BoundingBox(x1=240, y1=340, x2=280, y2=380, label="casting"),
    ]
    state1 = counter.update(f1)
    assert state1.total_count == 0
    assert len(state1.tracked_items) == 3

    # Frame 2: approaching line (center x = 290)
    f2 = [
        BoundingBox(x1=270, y1=100, x2=310, y2=140, label="casting"),
        BoundingBox(x1=270, y1=220, x2=310, y2=260, label="casting"),
        BoundingBox(x1=270, y1=340, x2=310, y2=380, label="casting"),
    ]
    state2 = counter.update(f2)
    assert state2.total_count == 0

    # Frame 3: crossed line (center x = 320)
    f3 = [
        BoundingBox(x1=300, y1=100, x2=340, y2=140, label="casting"),
        BoundingBox(x1=300, y1=220, x2=340, y2=260, label="casting"),
        BoundingBox(x1=300, y1=340, x2=340, y2=380, label="casting"),
    ]
    state3 = counter.update(f3)
    assert state3.total_count == 3

    # Frame 4: moving further (center x = 350) - must NOT double count
    f4 = [
        BoundingBox(x1=330, y1=100, x2=370, y2=140, label="casting"),
        BoundingBox(x1=330, y1=220, x2=370, y2=260, label="casting"),
        BoundingBox(x1=330, y1=340, x2=370, y2=380, label="casting"),
    ]
    state4 = counter.update(f4)
    assert state4.total_count == 3


def test_welding_zone_debounce_ignores_worker_hand_and_counts_confirmed_part():
    roi = BoundingBox(x1=100, y1=100, x2=500, y2=400, label="roi")
    zone_counter = WeldingZoneCounter(roi=roi, confirm_frames=4, max_match_distance=60.0)

    # Worker's hand/tool enters zone briefly for 2 frames then leaves -> count stays 0
    hand_box = [BoundingBox(x1=200, y1=200, x2=260, y2=260, label="part")]
    assert zone_counter.update(hand_box).total_count == 0
    assert zone_counter.update(hand_box).total_count == 0
    assert zone_counter.update([]).total_count == 0

    # Worker places a real welded part that stays for 6 frames -> counted once at frame 4
    part_box = [BoundingBox(x1=250, y1=220, x2=330, y2=300, label="part")]
    assert zone_counter.update(part_box).total_count == 0  # frame 1
    assert zone_counter.update(part_box).total_count == 0  # frame 2
    assert zone_counter.update(part_box).total_count == 0  # frame 3
    s4 = zone_counter.update(part_box)                     # frame 4 -> confirmed!
    assert s4.total_count == 1
    assert s4.tracked_items[0].counted is True

    # Stays in zone for frames 5 and 6 -> still 1 (idempotent)
    assert zone_counter.update(part_box).total_count == 1
    assert zone_counter.update(part_box).total_count == 1
