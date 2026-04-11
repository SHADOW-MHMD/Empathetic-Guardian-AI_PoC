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
        elif scenario == "anxious":
            return {
                "hr": 90.0,
                "hrv": 35.0,
                "voice_tremor": 0.3,
                "sentiment": -0.2,
                "text": "I'm really worried about the test tomorrow. What if I fail?"
            }
        elif scenario == "scared":
            return {
                "hr": 120.0,
                "hrv": 20.0,
                "voice_tremor": 0.6,
                "sentiment": -0.7,
                "text": "I heard a strange noise outside. I'm terrified something bad is going to happen."
            }
        elif scenario == "crying":
            return {
                "hr": 85.0,
                "hrv": 40.0,
                "voice_tremor": 0.4,
                "sentiment": -0.8,
                "text": "I just lost my best friend. I don't know how to go on without them."
            }
        elif scenario == "heavy_hearted":
            return {
                "hr": 65.0,
                "hrv": 50.0,
                "voice_tremor": 0.1,
                "sentiment": -0.5,
                "text": "I just don't see the point today. Everything feels so empty."
            }
        else:
            raise ValueError(f"Unknown scenario: {scenario}")
