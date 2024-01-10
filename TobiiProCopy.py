# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 et:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
from smile.clock import *
from smile.clock import Clock
from smile.log import LogWriter, log2dl
import tobii_research as tr

#import tobii_research_addons
# from tba import vectormath, ScreenBasedCalibrationValidation
# from tobii_research_addons import *
import ctypes, os
import time
import numpy as np
# import pandas as pd
import pickle
import math

class TobiiProTracker():

    """
    Helper class for calibrating and recording TobiiPro data.
    """
    def __init__(self, tracker_id=None):
        # holds the most recent 1800 samples of gaze data (3 seconds worth at 600hz)
        self.gaze_positions = np.zeros([1800,2])

        # consists of all but the most recent 600 samples of gaze positions
        # self.occ_buffer = self.gaze_positions[-1200:]

        # length of a fixation -- currently 1/4 second
        self.fix_length = 200

        # how close our current gaze position can be to a given point of
        # fixation to update gabor position (technically radius squared)
        self.radius = 0.007

        # check to see if we can update position of gabor
        self.check = False

        # not writing to file, yet
        self._log_file = None

        # not yet tracking
        self.tracking = False

        # not yet calibrated
        self.calibration_result = None

        self.sample = None
        self.gaze_pos = None

        # pick a tracker
        if tracker_id:
            # search for that eyetracker only
            self.eyetrackers = [t for t in tr.find_all_eyetrackers()
                                if t.serial_number == tracker_id]
        else:
            # get a list of all trackers (we'll pick the first)
            self.eyetrackers = tr.find_all_eyetrackers()

        # pick the first if we have one
        if self.eyetrackers:
            self.eyetracker = self.eyetrackers[0]
        else:
            # raise a warning
            print('WARNING! No matching eyetracker found!')
            self.eyetracker = None
            while self.eyetracker is None:
                try:
                    print('Retry')
                    self.eyetrackers = tr.find_all_eyetrackers()
                    self.eyetracker = self.eyetrackers[0]
                except:
                    time.sleep(2)

    def _on_gaze_data(self, gaze_data):
        # add times for sync
        gaze_data.update({'smile_time': clock.now(),
                          'tracker_time': tr.get_system_time_stamp(),
                          'buffer_on': self.check})

        # append data to stream
        # self.gaze.append(gaze_data)
        self.sample = gaze_data

        # if we have data from at least one left or right eye
        if self.sample["right_gaze_origin_validity"] or self.sample["left_gaze_origin_validity"]:
            x = np.nanmean(np.asarray([gaze_data['left_gaze_point_on_display_area'][0],
                    gaze_data['right_gaze_point_on_display_area'][0]]))
            y = np.nanmean(np.asarray([gaze_data['left_gaze_point_on_display_area'][1],
                    gaze_data['right_gaze_point_on_display_area'][1]]))
            self.gaze_pos = [x, y]
            self.valid = True
        # else, skip this sample
        else:
            self.valid = False

        # NOTE: if invalid, it will assume the fixation location is unchanged
        # from the last valid loction
        self.gaze_positions = np.roll(self.gaze_positions, 2)
        self.gaze_positions[0] = self.gaze_pos
        self.occ_buffer = self.gaze_positions # determines length of occ buffer

        self.fixations = np.where(np.sum((self.occ_buffer-self.gaze_pos)**2,
                                         axis=1) < self.radius)[0]

        # if the length of the current fixation buffer is longer than our fixation length
        self.check = len(self.fixations) >= self.fix_length

        # move the gabor
        gaze_data.update({'buffer_on': self.check,
                          'valid': self.valid})

        # write to file if writing
        if self._log_file:
            self._log_file.write_record(gaze_data)


    def start_tracking(self):
        # can only record if there is an eytracker
        if self.tracking:
            print('WARNING! Already tracking with eyetracker.')
            self.gaze = []
        else:
            self.gaze = []
            # subscribe to the eyetracker stream
            self.eyetracker.subscribe_to(tr.EYETRACKER_GAZE_DATA,
                                         self._on_gaze_data,
                                         as_dictionary=True)
            time.sleep(1) # not sure why they want this
            self.tracking = True


    def stop_tracking(self):
        if self.tracking:
            # unsubscribe from the stream
            self.eyetracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA)
            self.tracking = False

            # close the file if recording
            self.stop_recording()
        else:
            print('WARNING! Not already recording.')


    def start_recording(self, filename):
        # set the logfile
        self._log_file = LogWriter(filename)

        # start tracking if not already (will reset gaze)
        self.start_tracking()


    def stop_recording(self):
        if self._log_file:
            # close it (flushing data)
            self._log_file.close()

            # set it to none to stop trying to write
            self._log_file = None

    def clear_gazebuffer(self):
        self.gaze_positions = np.zeros([600,2])
    ############################################################################
    # Calibration Code
    def calibration_mode_on(self):
        self.calibration = tr.ScreenBasedCalibration(self.eyetracker)
        self.calibration.enter_calibration_mode()

    def calibration_collect_data(self,point):
        self.calibration.collect_data(point[0],point[1])

    def calibration_compute_apply(self):
        self.calibration_result = self.calibration.compute_and_apply()

    def calibration_mode_off(self):
        self.calibration.leave_calibration_mode()
    def calibration_save(self,filename='saved_calibration.bin'):
        # Save the calibration to file.
        with open(filename, "wb") as f:
            calibration_data = self.eyetracker.retrieve_calibration_data()
            # None is returned on empty calibration.
            if calibration_data is not None:
                print("Saving calibration to file for eye tracker with serial number {0}.".format(self.eyetracker.serial_number))
                f.write(self.eyetracker.retrieve_calibration_data())
            else:
                print("No calibration available for eye tracker with serial number {0}.".format(self.eyetracker.serial_number))
    ############################################################################
    # Validation Code
    def validation_compute(self,gaze_file,trial_info):
        eye = pd.DataFrame(log2dl(gaze_file))
        log_times = [(i['appear_time_time']['time'],
                      i['disappear_time_time']['time']) for i in trial_info]
        print(log_times)
        # storage for target location & corresponding samples
        g_code = []
        # sorting gaze data by target
        for trial in log_times:
            samples = eye[(eye.smile_time>=trial[0])&
                          (eye.smile_time<trial[1])]
            left_x = list(samples.left_gaze_point_on_display_area_0)
            left_y = list(samples.left_gaze_point_on_display_area_1)
            right_x = list(samples.right_gaze_point_on_display_area_0)
            right_y = list(samples.right_gaze_point_on_display_area_1)
            avg_x = [np.average([left_x[i],right_x[i]]) for i in range(len(left_x))]
            avg_y = [np.average([left_y[i],right_y[i]]) for i in range(len(left_x))]

            target_x = trial_info[log_times.index(trial)]['x']
            target_y = trial_info[log_times.index(trial)]['y']
            tri = {'target_x': target_x,
                   'target_y': target_y,
                   'gaze_data': []}

            for i in range(len(avg_x)):
                # if avg_x[i] >0 or avg_y[i] != None:
                if math.isnan(avg_x[i]) != True and math.isnan(avg_y[i]) != True:
                    tri['gaze_data'].append({'x':avg_x[i], 'y':avg_y[i]})
            # add to storage list
            g_code.append(tri)
        pickle.dump(g_code,open('validation_pickle.p','wb'))
        pickle.dump(trial_info,open('trial_info.p','wb'))
        self.validation_data = g_code
