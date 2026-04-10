class SyntheticHuman:
    def get_state(self, scenario):
        if scenario == "calm":
            return {
                "hr": 70.0,
                "hrv": 60.0,
                "voice_tremor": 0.0,
                "sentiment": 0.8,
                "text": "I had a pretty normal day at school today."
            }
        elif scenario == "panic":
            return {
                "hr": 140.0,
                "hrv": 15.0,
                "voice_tremor": 0.8,
                "sentiment": -0.9,
                "text": "I can't breathe, everything is going wrong, I don't know what to do!"
            }
        else:
            raise ValueError(f"Unknown scenario: {scenario}")
