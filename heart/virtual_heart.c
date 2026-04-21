#include <math.h>
#include <stdio.h>


typedef struct {
    float stress;
    float fear;
    float sadness;
    float happiness;
    float motivation;
    float overthinking;
    float heart_rate;
    float hrv;
} VirtualHeart;


static float clampf(float value, float min_value, float max_value) {
    if (value < min_value) {
        return min_value;
    }
    if (value > max_value) {
        return max_value;
    }
    return value;
}


void init_heart(VirtualHeart *h) {
    if (!h) {
        return;
    }

    h->stress = 20.0f;
    h->fear = 12.0f;
    h->sadness = 18.0f;
    h->happiness = 55.0f;
    h->motivation = 58.0f;
    h->overthinking = 20.0f;
    h->heart_rate = 72.0f;
    h->hrv = 62.0f;
}


void update_heart(VirtualHeart *h, float stress_input, float positive_input) {
    if (!h) {
        return;
    }

    /* Input expected in [0, 1]. */
    stress_input = clampf(stress_input, 0.0f, 1.0f);
    positive_input = clampf(positive_input, 0.0f, 1.0f);

    /* Decay + stimulus updates. */
    h->stress = (h->stress * 0.97f) + (stress_input * 18.0f) - (positive_input * 4.0f);
    h->happiness = (h->happiness * 0.94f) + (positive_input * 20.0f) - (stress_input * 7.0f);
    h->fear = (h->fear * 0.95f) + (stress_input * 16.0f) + (h->stress * 0.05f);
    h->sadness = (h->sadness * 0.96f) + (stress_input * 10.0f) - (positive_input * 6.0f);

    h->stress = clampf(h->stress, 0.0f, 100.0f);
    h->happiness = clampf(h->happiness, 0.0f, 100.0f);
    h->fear = clampf(h->fear, 0.0f, 100.0f);
    h->sadness = clampf(h->sadness, 0.0f, 100.0f);

    /* Derived variables. */
    h->overthinking = clampf((0.65f * h->stress) + (0.35f * h->sadness), 0.0f, 100.0f);
    h->motivation = clampf(50.0f + (0.60f * h->happiness) - (0.70f * h->stress), 0.0f, 100.0f);

    /* Fear + stress increase HR, and higher stress lowers HRV. */
    h->heart_rate = clampf(70.0f + (0.32f * h->stress) + (0.24f * h->fear) - (0.08f * h->happiness), 48.0f, 165.0f);
    h->hrv = clampf(82.0f - (0.48f * h->stress) - (0.25f * h->fear) + (0.12f * h->happiness), 10.0f, 120.0f);
}


const char *interpret_emotion(VirtualHeart h) {
    if (h.stress > 70.0f || h.overthinking > 68.0f) {
        return "stressed and overwhelmed";
    }
    if (h.sadness > 64.0f) {
        return "sad and withdrawn";
    }
    if (h.fear > 62.0f) {
        return "anxious and fearful";
    }
    if (h.happiness > 70.0f && h.motivation > 60.0f) {
        return "hopeful and motivated";
    }
    if (h.motivation < 35.0f) {
        return "low-energy and discouraged";
    }
    return "emotionally mixed but stable";
}
