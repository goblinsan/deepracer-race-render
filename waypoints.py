import matplotlib.pyplot as plt
import numpy as np
# Track Name from Tracks List
track_name = "reinvent_base"
# Location of tracks folder
absolute_path = "."
# Get waypoints from numpy file
waypoints = np.load("%s/%s.npy" % (absolute_path, track_name))
# Get number of waypoints
print("Number of waypoints = " + str(waypoints.shape[0]))
# Plot waypoints
for i, point in enumerate(waypoints):
    if i < 70:
        inner_waypoint = (point[0], point[1])
        waypoint = (point[2], point[3])
        outter_waypoint = (point[4], point[5])
        plt.scatter(inner_waypoint[0], inner_waypoint[1])
        plt.scatter(waypoint[0], waypoint[1])
        plt.scatter(outter_waypoint[0], outter_waypoint[1])
        print("Waypoint " + str(i) + ": " + str(waypoint))

plt.show()