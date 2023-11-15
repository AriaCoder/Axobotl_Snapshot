# AXOBOTL Python Code
# Axolotl Robotics team 4028X for 2023-2024 VEX IQ Full Volume Challenge
from vex import *


class Bot:
    MODES = ["MANUAL", "AUTO_RED", "AUTO_BOTLEFT", "AUTO_BOTRIGHT"]
    MODE_COLORS = [Color.BLACK, Color.RED, Color.YELLOW_GREEN, Color.PURPLE]
    MODE_PEN_COLORS = [Color.WHITE, Color.WHITE, Color.BLACK, Color.WHITE]

    def __init__(self):
        self.isAutoRunning = False
        self.modeNumber = 0
        self.isManualStarted = False
        self.cancelCalibration = False

    def setup(self):
        self.brain = Brain()
        self.inertial = Inertial()
        self.controller = Controller()
        self.setupPortMappings()
        self.setupController()
        self.setupDrive()
        self.setupIntake()
        self.setupBasket()
        self.setupSelector()
        self.setupAuto()  # Do this last due to calibration
        
    def setupPortMappings(self):
        self.motorLeft = Motor(Ports.PORT1,1,True)
        self.motorRight = Motor(Ports.PORT6,1, False)
        self.intakeLeft = Motor(Ports.PORT7,1,True)
        self.intakeRight = Motor(Ports.PORT3)
        self.basketLeft = Motor(Ports.PORT8)
        self.basketRight = Motor(Ports.PORT2)
        self.healthLed = Touchled(Ports.PORT9)
        self.basketDownBumper = Bumper(Ports.PORT4)
        self.basketUpBumper = Bumper(Ports.PORT5)
        self.driveTrain = None  # Default is MANUAL mode, no driveTrain

    def setupIntake(self):
        self.intake = MotorGroup(self.intakeLeft, self.intakeRight)
        self.intake.set_velocity(100, PERCENT)

    def setupBasket(self):
        self.basketLeft.set_reversed(True)
        self.basket = MotorGroup(self.basketLeft, self.basketRight)
        self.basket.set_velocity(100, PERCENT)
        self.basketUpBumper.pressed(self.onBasketUpBumper)
        self.basketDownBumper.pressed(self.onBasketDownBumper)

    def setupController(self):
        self.controller.buttonLUp.pressed(self.onLUp)
        self.controller.buttonLDown.pressed(self.onLDown)
        self.controller.buttonFUp.pressed(self.onFUp)
        self.controller.buttonRUp.pressed(self.onRUp)
        self.controller.buttonRUp.released(self.onRUpReleased)
        self.controller.buttonRDown.pressed(self.onRDown)
        self.controller.buttonRDown.released(self.onRDownReleased)
        # Delay to make sure events are registered correctly.
        wait(15, MSEC)

    def setupSelector(self):
        self.brain.buttonRight.pressed(self.onBrainButtonRight)
        self.brain.buttonLeft.pressed(self.onBrainButtonLeft)
        self.brain.buttonCheck.pressed(self.onBrainButtonCheck)

    def print(self, message):
        screenColor = Bot.MODE_COLORS[self.modeNumber]
        penColor = Bot.MODE_PEN_COLORS[self.modeNumber]
        self.brain.screen.set_font(FontType.MONO20)
        self.brain.screen.set_pen_color(penColor)
        self.brain.screen.set_fill_color(screenColor)
        self.brain.screen.print(message)
        self.brain.screen.new_line()

    def onBrainButtonCheck(self):
        if self.isAutoRunning:
            self.print("Already running")
        else:
            self.isAutoRunning = True
            if self.modeNumber == 1:
                self.runAutoRed()
            elif self.modeNumber == 2:
                self.runAutoLeft()
            elif self.modeNumber == 3:
                self.runAutoRight()
            else:
                self.isAutoRunning = False
                self.runManual()
            self.isAutoRunning = False
            self.print("Done")

    def onBrainButtonRight(self):
        self.applyMode(self.modeNumber + 1)

    def onBrainButtonLeft(self):
        self.applyMode(self.modeNumber - 1)

    def applyMode(self, newMode):
        self.cancelCalibration = True
        if self.isAutoRunning:
            self.print("Running auto already")
        elif self.isManualStarted:
            self.print("In manual mode")
        else:
            self.modeNumber = newMode % len(Bot.MODES)
            self.fillScreen(Bot.MODE_COLORS[self.modeNumber])

    def fillScreen(self, screenColor):
        self.brain.screen.set_pen_color(screenColor)
        self.brain.screen.clear_screen()
        self.brain.screen.set_font(FontType.MONO20)
        self.brain.screen.set_fill_color(screenColor)
        self.brain.screen.draw_rectangle(0, 0, 170, 100, screenColor)
        self.brain.screen.set_cursor(1, 1)
        self.print(Bot.MODES[self.modeNumber])

    def onLUp(self): 
        self.basket.spin(FORWARD, 100, PERCENT)
        self.intake.spin(FORWARD, 100, PERCENT)

    def onEUp(self):
        pass

    def onLDown(self):
        self.intake.spin(REVERSE, 100, PERCENT)

    def onFUp(self):
        self.stopAll()

    def onRUp(self):
        self.intake.stop()
        while self.controller.buttonRUp.pressing() and not self.basketUpBumper.pressing():
            self.basket.spin(REVERSE, 100, PERCENT)
            wait(1000, MSEC)
        self.basket.stop(COAST)

    def onRUpReleased(self):
        self.basket.stop(COAST)  # Let it drift down

    def onRDown(self):
        while self.controller.buttonRDown.pressing() and not self.basketDownBumper.pressing():
            self.basket.spin(FORWARD, 100, PERCENT)
            wait(1000, MSEC)
        self.basket.stop(COAST)

    def onRDownReleased(self):
        self.basket.stop(COAST)  # COAST allows basket to drop on its own

    def onBasketUpBumper(self):
        self.basket.stop(COAST)

    def onBasketDownBumper(self):
        self.basket.stop(COAST)

    def setupDrive(self):
        self.motorLeft.set_velocity(0, PERCENT)
        self.motorLeft.set_max_torque(100, PERCENT)
        self.motorLeft.spin(REVERSE)
        self.motorRight.set_velocity(0, PERCENT)
        self.motorRight.set_max_torque(100, PERCENT)
        self.motorRight.spin(REVERSE)

    def stopAll(self):
        if self.driveTrain is not None:
            self.driveTrain.stop(COAST)
        self.intake.stop(COAST)
        self.basket.stop(COAST)
        self.print("STOPPING")

    def checkHealth(self):
        # Copied from our code for Slapshot 2022-23 season
        color = Color.RED
        capacity = self.brain.battery.capacity()
        if capacity > 85:
            color = Color.BLUE
        elif capacity > 75:
            color = Color.GREEN
        elif capacity > 60:
            color = Color.ORANGE
        else:
            color = Color.RED
        self.healthLed.set_color(color)

    def setupAuto(self):
        # Use DriveTrain in autonomous. Easier to do turns.
        # Last updated on Nov 14, 2023:
        # Track width: 7-7/8 inches(7.875)
        # Wheel base : 6-1/2 inches(6.5)
        if not self.driveTrain:
            self.driveTrain = DriveTrain(self.motorLeft,
                                            self.motorRight,
                                            wheelTravel=200,
                                            trackWidth=200.025,
                                            wheelBase=165.1,
                                            units=DistanceUnits.MM,
                                            externalGearRatio=1)  # TODO: Is this correct?
            self.print("Calibrating...")
            self.inertial.calibrate()
            countdown = 3000/50  # Wait for no longer than 3 seconds
            while self.inertial.is_calibrating() and countdown > 0 and not self.cancelCalibration:
                wait(50, MSEC)
                countdown = countdown - 1
            if self.cancelCalibration:
                self.print("Cancelled Calibration!")
            elif countdown > 0 and not self.inertial.is_calibrating():
                self.print("Calibrated")
        else:
            self.print("FAILED Calibration")
                    
    def updateLeftDrive(self, joystickTolerance: int):
        velocity: float = self.controller.axisA.position()
        if math.fabs(velocity) > joystickTolerance:
            self.motorLeft.set_velocity(velocity, PERCENT)
            self.isManualStarted = True
        else:
            self.motorLeft.set_velocity(0, PERCENT)

    def updateRightDrive(self, joystickTolerance: int):
        velocity: float = self.controller.axisD.position()
        if math.fabs(velocity) > joystickTolerance:
            self.motorRight.set_velocity(velocity, PERCENT)
            self.isManualStarted = True
        else:
            self.motorRight.set_velocity(0, PERCENT)

    def autoDrive(self, direction, distance, units=DistanceUnits.IN,
                  velocity=100, units_v:VelocityPercentUnits=VelocityUnits.RPM,
                  wait=True, timeoutSecs=100):
        if self.driveTrain is not None:
            if timeoutSecs != 100:
                self.driveTrain.set_timeout(timeoutSecs, TimeUnits.SECONDS)
            self.driveTrain.drive_for(direction, distance, units, velocity, units_v, wait)
            if timeoutSecs != 100:  # Restore timeout for future driveTrain users
                self.driveTrain.set_timeout(100, TimeUnits.SECONDS)

    def autoTurn(self, direction, angle, units=RotationUnits.DEG,
                 velocity=50, units_v:VelocityPercentUnits=VelocityUnits.PERCENT, wait=True,
                 timeoutSecs=100):
        if self.driveTrain is not None:
            if timeoutSecs != 100:
                self.driveTrain.set_timeout(timeoutSecs, TimeUnits.SECONDS)
            self.driveTrain.turn_for(direction, angle / 2, units, velocity, units_v, wait)
            if timeoutSecs != 100:  # Restore timeout for future driveTrain users
                self.driveTrain.set_timeout(100, TimeUnits.SECONDS)

    # TODO: Add a parameter for green vs. purple blocks?
    def autoBasket(self, up: bool = True):
        self.basket.set_timeout(3000, MSEC)
        # Let the up/down basket bumpers take care of stopping the basket
        if up:
            self.basket.spin_for(REVERSE, 9000, RotationUnits.DEG, 100, PERCENT)
        else:
            self.basket.spin_for(FORWARD, 9000, RotationUnits.DEG, 100, PERCENT)

    def run(self):
        self.setup()
        self.checkHealth()
        self.runManual()

    def runManual(self):
        while(True):
            self.updateLeftDrive(5)
            self.updateRightDrive(5)
            sleep(50)

    def runAutoRed(self):
        self.autoDrive(FORWARD, 500, MM, 100, PERCENT, wait=True, timeoutSecs=6)
        self.autoDrive(REVERSE, 500, MM, 100, PERCENT, wait=True)  # Return home

    def runAutoLeft(self):           
        self.intake.spin(FORWARD, 100, PERCENT)
        self.autoDrive(FORWARD, 350, MM, 25, PERCENT)
        self.autoTurn(RIGHT, 20, DEGREES, 50, PERCENT)

        self.autoDrive(REVERSE, 360, MM, 50, PERCENT, wait=True, timeoutSecs=2)
        # Sometimes the drive fails... :-(
       # self.autoDrive(FORWARD, 150, MM, 75, PERCENT, wait=rue, timeoutSecs=2)
       # self.autoTurn(LEFT, 15, DEGREES, 50, PERCENT, wait=true, timeoutSecs=2)
        #self.autoDrive(REVERSE, 150, MM, 75, PERCENT, wait=TRue, timeoutSecs=2)

        self.basket.set_timeout(2, SECONDS)
        self.basket.spin_for(REVERSE, 2.5, TURNS)
        self.basket.set_timeout(60, SECONDS)

        # Bump to dislodge extra blocks
        wait(2, SECONDS)
        self.basket.set_timeout(1, SECONDS)
        self.autoDrive(FORWARD, 150, MM, 50, PERCENT, wait=True, timeoutSecs=2)
        self.autoDrive(REVERSE, 150, MM, 50, PERCENT, wait=True, timeoutSecs=2)
        self.stopAll()

    def runAutoRight(self):
        self.intake.spin(FORWARD, 100, PERCENT)
        self.autoDrive(FORWARD, 350, MM, 50,PERCENT)
        self.autoDrive(REVERSE, 150, MM, 50, PERCENT)
        

        # Sometimes the turn doesn't succeed?
        if self.driveTrain is not None:
            self.driveTrain.set_timeout(3, SECONDS)

        self.autoTurn(LEFT, 50, DEGREES, 20,PERCENT)
        self.autoDrive(REVERSE, 330, MM, 50, PERCENT, 75)
        self.basket.set_timeout(2, SECONDS)
        self.basket.spin_for(REVERSE, 10.8, TURNS)
        self.autoDrive(FORWARD, 3, MM)
        self.autoDrive(REVERSE, 3, MM)
        self.stopAll()

# Where it all begins!    
bot = Bot()
bot.run()
