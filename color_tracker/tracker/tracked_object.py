from collections import deque


class TrackedObject(object):
    def __init__(self, id, max_num_of_points=None):
        self._obj_id = id
        self._tracked_points = None
        self._max_num_of_points = max_num_of_points

        self._create_point_list()

    def _create_point_list(self):
        self._tracked_points = None
        if self._max_num_of_points:
            self._tracked_points = deque(maxlen=self._max_num_of_points)
        else:
            self._tracked_points = deque()

    def add_point(self, point):
        self._tracked_points.append(point)

    def get_tracked_points(self):
        return self._tracked_points

    def reset_tracked_points(self):
        self._create_point_list()

    def get_last_tracker_point(self):
        if len(self._tracked_points) > 0:
            return self._tracked_points[-1]
        else:
            return None
