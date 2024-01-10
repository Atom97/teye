#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##


# load all the states
from smile.common import *
from smile.log import log2dl
from smile.scale import scale as s
import tobiiresearch as tr
import TobiiProCopy
from TobiiProCopy import TobiiProTracker

from eye_listgen import gen_eyedot_blocks
from validation_trial import Trial, GetResponse
from tobii_research_addons import ScreenBasedCalibrationValidation, Point2
import config as CogBatt_config
import eye_config as Eye_config

# from tba import ScreenBasedCalibrationValidation, Point2
# eye tracker
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import mm

import pandas as pd

# define calibration variables; these can be moved to a config file
sample_count = 200
timeout_ms = 1000
# # targets for calibration/validation
# targets = [(0.25, 0.5),
#            (0.75, 0.5),
#            (0.2, 0.2),
#            (0.8, 0.8),
#            (0.5, 0.2),
#            (0.2, 0.8),
#            (0.5, 0.8),
#            (0.8, 0.2),
#            (0.5, 0.5)]
targets = [(0.15, 0.5),
           (0.85, 0.5),
           (0.1, 0.1),
           (0.9, 0.9),
           (0.5, 0.1),
           (0.1, 0.9),
           (0.5, 0.9),
           (0.9, 0.1),
           (0.5, 0.5)]


points_to_collect = [Point2(x,y) for x,y in targets]
cal_keys = [str(i) for i in points_to_collect]
cal_dict = {}
for i in cal_keys:
    ind = cal_keys.index(i)
    cal_dict[i] = {'target': targets[ind],
                   'point': points_to_collect[ind]}

@Subroutine
def TobiiTrackbox(self):
    """
    Tobii Trackbox
    """
    tt = TobiiProCopy.TobiiProTracker()
    Tobii = Ref.object(tt)
    screen_width = self._exp.screen.width
    screen_height = self._exp.screen.height
    screen_center_x = self._exp.screen.center_x
    screen_center_y = self._exp.screen.center_y
    self.targets = targets
    val_aoe = 0.05

    self.x0 = 0
    self.y0 = 0
    ################
    # Track Box
    # Give participant and experimentor(s) feedback participant's
    # position in the eyetracker's viewing area
    with Parallel():
        # Guiding rectangles
        small_rectangle = Line(rectangle=((screen_width/2-(screen_width*.25)/2.),
                                         (screen_height/2-(screen_height*.25)/2.),
                                         screen_width*.25,
                                         screen_height*.25),
                              color='blue',
                              width=2)
        big_rectangle = Line(rectangle=((screen_width/2-(screen_width*.75)/2.),
                                         (screen_height/2-(screen_height*.75)/2.),
                                         screen_width*.75,
                                         screen_height*.75),
                              color='blue',
                              width=2)
        directions = Label(text='Find a comfortable position within view\n\of the eyetracker. The box will turn green\n\when you are in a good position.',
                        halign='left',
                        center_x=screen_center_x,
                        center_y=screen_height-(screen_height*.1),
                        font_size=40)


    # updating trackbox
    with UntilDone():
        Wait(1.0)
        # start_tracking
        with If(Tobii.tracking==False):
            Func(Tobii.start_tracking)
        # give eyetracker time to start
        Wait(1.5)
        with Parallel():
            # left eye representation
            foc_l = Ellipse(color='red',
                            size=[screen_height*.1,screen_height*.1],
                            center_x=screen_center_x-(screen_height*.1),
                            center_y=screen_center_y)
            # right eye representation
            foc_r = Ellipse(color='red',
                            size=[screen_height*.1,screen_height*.1],
                            center_x=screen_center_x+(screen_height*.1),
                            center_y=screen_center_y)
            # transluscent rectangle that grows/shrinks with head distance
            rect = Rectangle(color=(1.,0.,0.,0.25),
                                     center_x=screen_center_x,
                                     center_y=screen_center_y,
                                     width=screen_width*(6./8),
                                     height=screen_height*(6./8))
        with UntilDone():
            with Loop():
                Wait(.05)
                # get gaze sample
                self.gaze_sample = Tobii.sample

                # calculating average distance from each eye to the screen
                left_distance = self.gaze_sample['left_gaze_origin_in_trackbox_coordinate_system'][2]
                right_distance = self.gaze_sample['right_gaze_origin_in_trackbox_coordinate_system'][2]
                # y_coordinate eye positions
                left_height = self.gaze_sample['left_gaze_origin_in_trackbox_coordinate_system'][1]
                right_height = self.gaze_sample['right_gaze_origin_in_trackbox_coordinate_system'][1]
                # x_coordinate eye positions
                left_x = self.gaze_sample['left_gaze_origin_in_trackbox_coordinate_system'][0]
                right_x = self.gaze_sample['right_gaze_origin_in_trackbox_coordinate_system'][0]

                # check gaze validity of both eyes
                with If((self.gaze_sample['right_gaze_origin_validity']==0) &
                        (self.gaze_sample['left_gaze_origin_validity']==1)):
                    with Parallel():
                        self.avg_distance = left_distance
                        UpdateWidget(foc_r, color='red',
                                     center_y=screen_height-(screen_height*left_height),
                                     center_x=screen_width-(screen_width*left_x) + 2*(screen_height*.1))
                        UpdateWidget(foc_l, color='green',
                                     center_y=screen_height-(screen_height*left_height),
                                     center_x=screen_width-(screen_width*left_x))
                with Elif((self.gaze_sample['right_gaze_origin_validity']==1) &
                          (self.gaze_sample['left_gaze_origin_validity']==0)):
                    with Parallel():
                        self.avg_distance = right_distance
                        UpdateWidget(foc_r, color='green',
                                     center_y=screen_height-(screen_height*right_height),
                                     center_x=screen_width-(screen_width*right_x))
                        UpdateWidget(foc_l, color='red',
                                     center_y=screen_height-(screen_height*right_height),
                                     center_x=screen_width-(screen_width*right_x) - 2*(screen_height*.1))
                with Else():
                    with Parallel():
                        self.avg_distance = (right_distance+left_distance)/2.
                        UpdateWidget(foc_r, color='green',
                                     center_y=screen_height-(screen_height*right_height),
                                     center_x=screen_width-(screen_width*right_x))
                        UpdateWidget(foc_l, color='green',
                                     center_y=screen_height-(screen_height*left_height),
                                     center_x=screen_width-(screen_width*left_x))
                with If((self.avg_distance > .25) & (self.avg_distance < .75)):

                    UpdateWidget(rect, width=(screen_width*self.avg_distance),
                                        height=(screen_height*self.avg_distance),
                                        color=(0.,1.,0.,.25))

                # Update transluscent rectangle color:
                # green = head is within eye tracker's viewing range
                # red = head is too close or too far
                with Elif((self.avg_distance < 0.25)):
                    UpdateWidget(rect, color=(1.,0.,0.,.25))
                with Elif((self.avg_distance > 0.75)):
                    UpdateWidget(rect, color=(1.,0.,0.,.25))
            with UntilDone():
                KeyPress()
    Func(Tobii.stop_tracking)


@Subroutine
def TobiiCalibration(self,
                     targets=targets,
                     filename='saved_calibration.bin'):
    """
    Tobii calibration
    """
    tt = TobiiProCopy.TobiiProTracker()
    Tobii = Ref.object(tt)
    screen_width = self._exp.screen.width
    screen_height = self._exp.screen.height
    screen_center_x = self._exp.screen.center_x
    screen_center_y = self._exp.screen.center_y
    self.targets = targets
    val_aoe = 0.05

    self.x0 = 0
    self.y0 = 0
    ################
    # Calibration

    Label(text='Calibration: Press ENTER to begin.', width=600, font_size=40)
    with UntilDone():
        KeyPress('ENTER')
    Wait(1.0)

    # Enter Calibration Mode
    Func(Tobii.calibration_mode_on)
    Wait(1.5)

    # loop over fixation points
    with Loop(targets) as target:
        # present fixation point
        dot = Image(source='spiral_2.png',
                    center_x=screen_width*target.current[0],
                    center_y=screen_height-screen_height*target.current[1],
                    size=(30,30))
        with UntilDone():
            Wait(until=dot.appear_time)
            # Give participant time to focus on target
            dot.rotate_origin = dot.center
            dot.slide(rotate=1000, duration=1.5)
            # Collect calibration gaze data
            cal = Func(Tobii.calibration_collect_data, target.current)

            rct = Rectangle(color=(1,1,1,0), duration=.000001)
            Wait(until=rct.disappear_time)
            # explode
            explode = dot.slide(duration=0.5,
                                width=50, height=50,
                                color=(0, 0, 0, 0))
            Wait(until=explode.finalize_time)

    # Compute and Apply calibration
    Func(Tobii.calibration_compute_apply)
    ResetClock()
    Wait(0.5)
    # Turn off calibration mode
    Func(Tobii.calibration_mode_off)
    # Save calibration
    Func(Tobii.calibration_save,filename)

    Label(text='Calibration : Press ENTER to end.', width=600, font_size=40)
    with UntilDone():
        KeyPress('ENTER')


@Subroutine
def TobiiValidation(self,config,run_num=0,screenshot=False):
    tt = TobiiProCopy.TobiiProTracker()
    Tobii = Ref.object(tt)
    # generate stimuli
    dots = Func(gen_eyedot_blocks, config)
    self.dots = dots.result

    Label(text='DESTROY THE DOTS.\npress a key to continue',
          font_size=config.FONT_SIZE)
    with UntilDone():
        KeyPress()


    self.cont_calibrate = True
    self.show_val = True
    with Loop(conditional=(self.cont_calibrate)):
        Wait(1.0)
        # Tobii calibrate

        # start_tracking
        with If(Tobii.tracking==False):
            Func(Tobii.start_tracking)
        Wait(2.0)
        # Func(Tobii.start_recording,'eye_validation.slog')
        Func(Tobii.start_recording,Ref.object(self._exp)._session_dir + '\\eye_validation' + Ref(str,run_num) + '.slog')
        Wait(2.0)
        self.validation_stor = []
        with Parallel():
            with Serial(blocking=False):
                with Parallel():
                    MouseCursor(blocking=False)
                    # loop over blocks and trials
                    with Serial():
                        with Loop(self.dots) as block:
                            self.block = block.current
                            with Loop(self.block) as dot:
                                Wait(0.5, jitter=.2)
                                # Perform trials
                                tri = Trial(config,
                                            stim=dot.current,
                                            center_x=self.exp.center_x,
                                            center_y=self.exp.center_y,
                                            screen_width=self.exp.screen.width,
                                            screen_height=self.exp.screen.height,
                                            tobii=Tobii)
                                self.validation_stor += [{'appear_time_time':tri.appear_time,
                                                          'disappear_time_time':tri.disappear_time,
                                                          'x':self.exp.screen.width*dot.current[0],
                                                          'y':self.exp.screen.height - (self.exp.screen.height*dot.current[1])}]
                                Log(point=dot.current,
                                    name='VAL',
                                    run_num=run_num,
                                    appear_time=tri.appear_time,
                                    disappear_time=tri.disappear_time)

                        self.cont_calibrate = False

            with Serial(blocking=False):
                with ButtonPress():
                    Button(text="Skip",
                           right=self.exp.screen.width,
                           bottom=0, width=s(config.SKIP_SIZE[0]),
                           height=s(config.SKIP_SIZE[1]), blocking=False,
                           font_size=s(config.SKIP_FONT_SIZE))
                self.cont_calibrate = False
                self.show_val = False

    Func(Tobii.stop_recording)
    Func(Tobii.stop_tracking)
    # Retrieve Validation Data
    with If(self.show_val==True):
        Func(Tobii.validation_compute,
             Ref.object(self._exp)._session_dir + '\\eye_validation' + Ref(str,run_num) + '.slog',
             self.validation_stor)
        validation_data = Tobii.validation_data

        center_x=self.exp.center_x
        center_y=self.exp.center_y
        screen_width=self.exp.screen.width
        screen_height=self.exp.screen.height
        # Present points and gaze samples
        with Parallel() as par:
            with Serial():
                with Loop(validation_data) as val:
                    with par.insert():
                        Ellipse(color='red',
                                size=(25,25),
                                center_x=val.current['target_x'],
                                center_y=val.current['target_y'])
                    samps = val.current['gaze_data'][-10:]
                    with Loop(samps) as point:
                        # with If(left_val[spot.i] == True):
                        with par.insert():
                            Ellipse(color='white',
                                    size=(10,10),
                                    center_x=Ref(int,screen_width*point.current['x']),
                                    center_y=Ref(int,screen_height-screen_height*point.current['y']))

        with UntilDone():
            KeyPress()
            with If(screenshot==True):
                Screenshot(filename='meta_exp.png')

@Subroutine
def TobiiTrackerSetup(self,
                      trackbox=True,
                      calibrate=True,
                      validate=True,
                      run_num=0):
    tt = TobiiProCopy.TobiiProTracker()
    Tobii = Ref.object(tt)
    with If(Tobii.tracking==True):
        Func(Tobii.stop_tracking)
    Wait(1.5)
    self.continue_calibrate = True
    with Loop(conditional=(self.continue_calibrate)):
        # Eye Trackbox
        with If(trackbox==True):
            TobiiTrackbox()
        Wait(1.5)
        # Calibrate eye tracker
        with If(calibrate==True):
            TobiiCalibration(filename=Ref.object(self._exp)._session_dir + '\\saved_calibration' + Ref(str,run_num) + '.bin')
        Wait(1.5)
        # Validation
        with If(validate==True):
            TobiiValidation(config=Eye_config,run_num=run_num)
        cal_redo = "Accept Calibration: Y or N"
        Label(text=cal_redo,
              font_size=s(CogBatt_config.SSI_FONT_SIZE),
              halign="center")
        with UntilDone():
            if CogBatt_config.TOUCH:
                with ButtonPress():
                    Button(size=self.exp.screen.size,
                           name="redo_calibration", text="",
                           left=0, bottom=0,
                           background_color=(0, 0, 0, 0))
            else:
                kp = KeyPress(["Y", "N"])
        with If(kp.pressed == "Y"):
            self.continue_calibrate = False
