"""
Strava Activity model for representing workout data.
"""


class Activity:
    """
    Represents a Strava activity with workout data.

    This class encapsulates all the necessary data for creating
    a workout activity in Strava via their API.
    """

    def __init__(
        self,
        name,
        activity_type,
        sport_type,
        start_date_local,
        elapsed_time,
        **kwargs
    ):
        self.name = name
        self.type = activity_type
        self.sport_type = sport_type
        # ISO 8601 formatted date time
        self.start_date_local = start_date_local.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        self.elapsed_time = elapsed_time

        # Optional attributes with defaults
        self.description = kwargs.get('description')
        self.distance = kwargs.get('distance')  # meters
        self.trainer = kwargs.get('trainer')
        self.commute = kwargs.get('commute')
        self.calories = kwargs.get('calories')
        self.max_heartrate = kwargs.get('max_heartrate')
        self.avg_heartrate = kwargs.get('avg_heartrate')

    def to_dict(self):
        """
        Convert the Activity instance to a dictionary for API submission.

        Returns:
            dict: Dictionary representation of the activity data
        """
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
            "avg_heartrate": self.avg_heartrate,
        }

    def get_activity_summary(self):
        """
        Get a summary description of the activity.

        Returns:
            str: Summary of the activity
        """
        return f"{self.name} - {self.sport_type} for {self.elapsed_time}s"
