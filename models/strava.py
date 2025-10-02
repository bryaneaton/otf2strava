class Activity:
    def __init__(self, name, type, sport_type, start_date_local, elapsed_time, description=None, distance=None, trainer=None, commute=None, calories=None, max_heartrate=None, avg_heartrate=None):
        self.name = name
        self.type = type
        self.sport_type = sport_type
        self.start_date_local = start_date_local.strftime("%Y-%m-%dT%H:%M:%S.%fZ") # ISO 8601 formatted date time
        self.elapsed_time = elapsed_time
        self.description = description
        self.distance = distance # meters
        self.trainer = trainer
        self.commute = commute
        self.calories = calories
        self.max_heartrate = max_heartrate
        self.avg_heartrate = avg_heartrate

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.type,
            "sport_type": self.sport_type,
            "start_date_local": self.start_date_local,
            "elapsed_time": self.elapsed_time,
            "description": self.description,
            "distance": self.distance,
            "trainer": self.trainer,
            "commute": self.commute,
            "calories": self.calories,
            "max_heartrate": self.max_heartrate,
            "avg_heartrate": self.avg_heartrate
        }