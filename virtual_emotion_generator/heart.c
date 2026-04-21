#include <math.h>
#include <stdlib.h>
#include <time.h>


typedef struct {
    float stress, happiness, sadness, fear;
    float motivation, overthinking;
    float heart_rate, hrv;
    float emotional_drift;
} VirtualHeart;


static int g_seeded = 0;


static float clampf(float value, float minimum, float maximum) {
    if (value < minimum) {
        return minimum;
    }
    if (value > maximum) {
        return maximum;
    }
    return value;
}


static float rand_unit(void) {
    return (float)rand() / (float)RAND_MAX;
}


static float rand_range(float minimum, float maximum) {
    return minimum + ((maximum - minimum) * rand_unit());
}


void init_heart(VirtualHeart *h) {
    if (!h) {
        return;
    }

    if (!g_seeded) {
        srand((unsigned int)time(NULL));
        g_seeded = 1;
    }

    h->stress = rand_range(15.0f, 45.0f);
    h->happiness = rand_range(35.0f, 65.0f);
    h->sadness = rand_range(10.0f, 40.0f);
    h->fear = rand_range(10.0f, 35.0f);
    h->motivation = rand_range(35.0f, 70.0f);
    h->overthinking = rand_range(10.0f, 40.0f);
    h->heart_rate = rand_range(62.0f, 84.0f);
    h->hrv = rand_range(48.0f, 82.0f);
    h->emotional_drift = rand_range(-4.0f, 4.0f);
}


void update_heart(VirtualHeart *h, float stress_input, float positive_input) {
    float noise_s;
    float noise_h;
    float noise_m;
    float target_hr;
    float target_hrv;

    if (!h) {
        return;
    }

    if (!g_seeded) {
        srand((unsigned int)time(NULL));
        g_seeded = 1;
    }

    if (h->heart_rate <= 0.0f || h->hrv <= 0.0f) {
        init_heart(h);
    }

    stress_input = clampf(stress_input, 0.0f, 1.0f);
    positive_input = clampf(positive_input, 0.0f, 1.0f);

    noise_s = rand_range(-1.0f, 1.0f);
    noise_h = rand_range(-1.0f, 1.0f);
    noise_m = rand_range(-1.0f, 1.0f);

    h->emotional_drift = (h->emotional_drift * 0.985f)
        + (0.15f * (h->stress - h->happiness) / 100.0f)
        + (0.10f * (h->sadness + h->fear) / 100.0f)
        + (noise_m * 1.2f);

    h->stress = h->stress
        + (-0.030f * h->stress)
        + (22.0f * stress_input)
        - (9.0f * positive_input)
        + (0.080f * h->overthinking)
        + (4.0f * noise_s)
        + (0.60f * h->emotional_drift);

    h->happiness = h->happiness
        + (-0.050f * h->happiness)
        + (20.0f * positive_input)
        - (11.0f * stress_input)
        - (0.040f * h->stress)
        + (3.2f * noise_h)
        - (0.45f * h->emotional_drift);

    h->sadness = h->sadness
        + (-0.035f * h->sadness)
        + (9.5f * stress_input)
        - (6.0f * positive_input)
        + (0.055f * h->stress)
        + (2.3f * rand_range(-1.0f, 1.0f))
        + (0.35f * h->emotional_drift);

    h->fear = h->fear
        + (-0.045f * h->fear)
        + (12.0f * stress_input)
        - (4.5f * positive_input)
        + (0.060f * h->stress)
        + (2.0f * rand_range(-1.0f, 1.0f))
        + (0.30f * h->emotional_drift);

    h->overthinking = h->overthinking
        + (-0.040f * h->overthinking)
        + (0.26f * h->sadness)
        + (0.16f * h->stress)
        - (0.08f * h->happiness)
        + (2.4f * rand_range(-1.0f, 1.0f))
        + (0.80f * h->emotional_drift);

    h->motivation = h->motivation
        + (-0.050f * h->motivation)
        + (0.34f * h->happiness)
        - (0.23f * h->stress)
        - (0.11f * h->sadness)
        + (2.2f * rand_range(-1.0f, 1.0f))
        - (0.50f * h->emotional_drift);

    h->stress = clampf(h->stress, 0.0f, 100.0f);
    h->happiness = clampf(h->happiness, 0.0f, 100.0f);
    h->sadness = clampf(h->sadness, 0.0f, 100.0f);
    h->fear = clampf(h->fear, 0.0f, 100.0f);
    h->overthinking = clampf(h->overthinking, 0.0f, 100.0f);
    h->motivation = clampf(h->motivation, 0.0f, 100.0f);
    h->emotional_drift = clampf(h->emotional_drift, -50.0f, 50.0f);

    target_hr = 64.0f
        + (0.34f * h->stress)
        + (0.22f * h->fear)
        - (0.12f * h->happiness)
        + (0.10f * h->emotional_drift);

    target_hrv = 78.0f
        - (0.42f * h->stress)
        - (0.20f * h->fear)
        + (0.16f * h->happiness)
        - (0.08f * h->emotional_drift);

    h->heart_rate = (h->heart_rate * 0.75f) + (target_hr * 0.25f) + rand_range(-1.4f, 1.4f);
    h->hrv = (h->hrv * 0.80f) + (target_hrv * 0.20f) + rand_range(-1.0f, 1.0f);

    h->heart_rate = clampf(h->heart_rate, 45.0f, 180.0f);
    h->hrv = clampf(h->hrv, 5.0f, 130.0f);
}


VirtualHeart get_state(VirtualHeart *h) {
    VirtualHeart empty = {0};
    if (!h) {
        return empty;
    }
    return *h;
}
