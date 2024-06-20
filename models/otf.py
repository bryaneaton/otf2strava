
class WorkoutData:
    def __init__(self, data, workout):
        self.workout = Workout(workout)
        self.heart_rate_data = HeartRateData(data['HeartRateData'])
        self.treadmill_data = TreadmillData(data['TreadmillData'])
        self.rower_data = RowerData(data['RowerData'])

class Workout:
    def __init__(self, data):
        self.studioNumber = data['studioNumber']
        self.studioName = data['studioName']
        self.classType = data['classType']
        self.activeTime = data['activeTime']
        self.coach = data['coach']
        self.memberUuId = data['memberUuId']
        self.classDate = data['classDate']
        self.totalCalories = data['totalCalories']
        self.avgHr = data['avgHr']
        self.maxHr = data['maxHr']
        self.avgPercentHr = data['avgPercentHr']
        self.maxPercentHr = data['maxPercentHr']
        self.totalSplatPoints = data['totalSplatPoints']
        self.redZoneTimeSecond = data['redZoneTimeSecond']
        self.orangeZoneTimeSecond = data['orangeZoneTimeSecond']
        self.greenZoneTimeSecond = data['greenZoneTimeSecond']
        self.blueZoneTimeSecond = data['blueZoneTimeSecond']
        self.blackZoneTimeSecond = data['blackZoneTimeSecond']
        self.stepCount = data['stepCount']
        self.classHistoryUuId = data['classHistoryUuId']
        self.classId = data['classId']
        self.dateCreated = data['dateCreated']
        self.dateUpdated = data['dateUpdated']
        self.isIntro = data['isIntro']
        self.isLeader = data['isLeader']
        self.memberEmail = data['memberEmail']
        self.memberName = data['memberName']
        self.memberPerformanceId = data['memberPerformanceId']
        self.minuteByMinuteHr = data['minuteByMinuteHr']
        self.source = data['source']
        self.studioAccountUuId = data['studioAccountUuId']
        self.version = data['version']
        self.workoutType = data['workoutType']

class HeartRateData:
    def __init__(self, data):
        self.class_time = data['ClassTime']
        self.class_type = data['ClassType']
        self.black_zone = data['BlackZone']
        self.blue_zone = data['BlueZone']
        self.green_zone = data['GreenZone']
        self.orange_zone = data['OrangeZone']
        self.red_zone = data['RedZone']
        self.calories = data['Calories']
        self.splat_point = data['SplatPoint']
        self.average_heart_rate = data['AverageHeartRate']
        self.average_heart_rate_percent = data['AverageHeartRatePercent']
        self.max_heart_rate = data['MaxHeartRate']
        self.max_percent_hr = data['MaxPercentHr']
        self.step_count = data['StepCount']

class TreadmillData:
    def __init__(self, data):
        self.avg_speed = data['AvgSpeed']
        self.max_speed = data['MaxSpeed']
        self.avg_incline = data['AvgIncline']
        self.max_incline = data['MaxIncline']
        self.avg_pace = data['AvgPace']
        self.max_pace = data['MaxPace']
        self.total_distance = data['TotalDistance']
        self.moving_time = data['MovingTime']
        self.elevation_gained = data['ElevationGained']

class RowerData:
    def __init__(self, data):
        self.avg_power = data['AvgPower']
        self.max_power = data['MaxPower']
        self.avg_speed = data['AvgSpeed']
        self.max_speed = data['MaxSpeed']
        self.avg_pace = data['AvgPace']
        self.max_pace = data['MaxPace']
        self.avg_cadence = data['AvgCadence']
        self.max_cadence = data['MaxCadence']
        self.total_distance = data['TotalDistance']
        self.moving_time = data['MovingTime']