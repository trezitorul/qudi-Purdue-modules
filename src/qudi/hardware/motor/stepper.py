""" 
Communicating serially to the stepper driver
"""

import time
import pyfirmata


class Stepper():
    def __init__(self, com_port, number_of_steps, motor_pin_1, motor_pin_2, motor_pin_3, motor_pin_4):
        
        self.board = pyfirmata.Arduino(com_port)                 # Change to your port

        self.step_numer = 0                     # which step the motor is on
        self.direction = 0                      # motor direction
        self.last_step_time = 0                 # time stamp in us of the last step taken
        self.number_of_steps = number_of_steps; # total number of steps for this motor

        # Arduino pins for the motor control connection:
        self.motor_pin_1 = motor_pin_1
        self.motor_pin_2 = motor_pin_2
        self.motor_pin_3 = motor_pin_3
        self.motor_pin_4 = motor_pin_4

        # pin_count is used by the step_motor() method:
        self.pin_count = 4

        self.stepsPerRevolution = number_of_steps
        self.rpm = 12
        self.position = 0


    def set_speed(self, what_speed):
        """Set speed of the motor

        Args:
            what_speed (float): speed of the motor
        """
        self.rpm=what_speed
        self.step_delay = 60 * 1000 * 1000 / self.number_of_steps / what_speed


    def step(self, steps_to_move):
        """ Stepping the motor by a number of steps

        Args:
            steps_to_move (int): steps to move
        """
        step_left = abs(steps_to_move)
        if (steps_to_move > 0): self.direction = 1
        if (steps_to_move < 0): self.direction = 0
        
        while (step_left > 0):
            # current_time = datetime.datetime.now().time()
            now = time.perf_counter_ns() / 1000
            if (now - self.last_step_time >= self.step_delay):
                self.last_step_time = now
                if (self.direction == 1):
                    self.step_numer += 1
                    if (self.step_numer == self.number_of_steps):
                        self.step_numer = 0
                else:
                    if (self.step_numer == 0):
                        self.step_numer = self.number_of_steps
                    self.step_numer -= 1
                    
                step_left -= 1
                
                self.step_motor(self.step_numer % 4)
    

    def step_motor(self, this_step):
        """ Communicating the driver to step the motor

        Args:
            this_step (int): how many steps
        """
        if (this_step == 0):
            self.board.digital[self.motor_pin_1].write(1)
            self.board.digital[self.motor_pin_2].write(0)
            self.board.digital[self.motor_pin_3].write(1)
            self.board.digital[self.motor_pin_4].write(0)
        elif (this_step == 1):
            self.board.digital[self.motor_pin_1].write(0)
            self.board.digital[self.motor_pin_2].write(1)
            self.board.digital[self.motor_pin_3].write(1)
            self.board.digital[self.motor_pin_4].write(0)
        elif (this_step == 2):
            self.board.digital[self.motor_pin_1].write(0)
            self.board.digital[self.motor_pin_2].write(1)
            self.board.digital[self.motor_pin_3].write(0)
            self.board.digital[self.motor_pin_4].write(1)
        elif (this_step == 3):
            self.board.digital[self.motor_pin_1].write(1)
            self.board.digital[self.motor_pin_2].write(0)
            self.board.digital[self.motor_pin_3].write(0)
            self.board.digital[self.motor_pin_4].write(1)

    def move_rel(self,  direction, step=1):
        """Moves stage in given direction (relative movement)

        Args:
            direction (int): 1 corresponds to up/right; -1 corresponds to down/left
            step (int, optional): number of steps. Defaults to 1.

        """
        self.step(step * direction)
        self.position += step * direction


    def get_pos(self):
        """Get current position

        Returns:
            int: current position
        """
        return self.position


    def get_rpm(self):
        """ Gets the current rpm for all connected axes.

        @return int : Current rpm
        """
        return self.rpm


    def set_rpm(self, rpm):
        """Set the rpm of the motor

        Args:
            rpm (int): round-per-minute
        """
        self.set_speed(rpm)
        self.rpm = rpm