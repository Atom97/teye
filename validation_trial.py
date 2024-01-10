from smile.common import *
from smile.scale import scale as s

import TobiiProCopy
from TobiiProCopy import TobiiProTracker

@Subroutine
def GetResponse(self,
                keys,
                base_time=None,
                correct_resp=None,
                duration=None):
    self.pressed = None
    self.rt = None
    self.correct = None
    self.press_time = None
    with Parallel():
        kp = KeyPress(base_time=base_time,
                      keys=keys,
                      correct_resp=correct_resp,
                      duration=duration,
                      blocking=False)
        with Serial(blocking=False):
            with ButtonPress(correct_resp=correct_resp,
                             base_time=base_time,
                             duration=duration,
                             ) as bp:
                Button(width=self.exp.screen.width*.45,
                       height=self.exp.screen.height,
                       name=keys[0], text="",
                       left=0, bottom=0, background_color=(0, 0, 0, 0))
                Button(width=self.exp.screen.width*.45, height=self.exp.screen.height,
                       name=keys[-1], text="", right=self.exp.screen.width,
                       bottom=0, background_color=(0, 0, 0, 0))

    self.pressed = Ref.cond((bp.pressed == ''), kp.pressed, bp.pressed)
    self.rt = Ref.cond((bp.pressed == ''), kp.rt, bp.rt)
    self.correct = Ref.cond((bp.pressed == ''), kp.correct, bp.correct)
    self.press_time = Ref.cond((bp.pressed == ''), kp.press_time, bp.press_time)

@Subroutine
def Trial(self,
          config,
          stim,
          center_x,
          center_y,
          screen_width,
          screen_height,
          tobii):

    Tobii = Ref.object(tobii)

    # present fixation points
    self.stim = stim
    x = screen_width*self.stim[0]
    y = screen_height - (screen_height*self.stim[1])
    dot = Ellipse(center_x=x,
                  center_y=y,
                  size=(s(config.DOT_SIZE),s(config.DOT_SIZE)),
                  color=self.stim[2])

    with UntilDone():
        Wait(until=dot.appear_time)
        # Present static fixation point until gaze lands within AOE of point
        self.stop = False
        with Loop(conditional=(self.stop==False)):
            Wait(.1)
            sample = Tobii.sample

            left = sample['left_gaze_point_on_display_area']
            right = sample['right_gaze_point_on_display_area']

            with If((self.stim[0]-config.AOE<=left[0]<=self.stim[0]+config.AOE)&
                    (self.stim[1]-config.AOE<=left[1]<=self.stim[1]+config.AOE)):
                Wait(.25)
                # draw transparent rectangle for timing
                rct = Rectangle(color=(1,1,1,0), duration=.000001)
                Wait(until=rct.disappear_time)
                explode = dot.slide(duration=0.5,
                                    width=50, height=50,
                                    color=(0, 0, 0, 0))
                Wait(until=explode.finalize_time)
                self.stop = True
            # with Elif((self.stim[0]-config.AOE<=right[0]<=self.stim[0]+config.AOE)&
            #         (self.stim[1]-config.AOE<=right[1]<=self.stim[1]+config.AOE)):
            #     # draw transparent rectangle for timing
            #     rct = Rectangle(color=(1,1,1,0), duration=.000001)
            #     Wait(until=rct.disappear_time)
            #     explode = dot.slide(duration=0.5,
            #                         width=50, height=50,
            #                         color=(0, 0, 0, 0))
            #     Wait(until=explode.finalize_time)
            #     self.stop = True
        # saving out timestamps for Logs
        self.appear_time = dot.appear_time
        Debug(app='yas')
        self.disappear_time = rct.appear_time


        Debug(OVER='yas')
