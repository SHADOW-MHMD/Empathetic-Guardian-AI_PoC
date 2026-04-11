/* somatic_engine_v2.c
   Full upgraded engine — all four systems integrated
   Compile: gcc -shared -o somatic_engine_v2.so -fPIC -O2 -lm somatic_engine_v2.c
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <stdint.h>

/* SECTION 1: NOISE + UNCERTAINTY SYSTEM */

static float gaussian_noise(float mean, float stddev) {
    static int   has_spare = 0;
    static float spare;
    if (has_spare) {
        has_spare = 0;
        return mean + stddev * spare;
    }
    has_spare = 1;
    float u, v, s;
    do {
        u = ((float)rand() / RAND_MAX) * 2.0f - 1.0f;
        v = ((float)rand() / RAND_MAX) * 2.0f - 1.0f;
        s = u*u + v*v;
    } while (s >= 1.0f || s == 0.0f);
    s = sqrtf(-2.0f * logf(s) / s);
    spare = v * s;
    return mean + stddev * u * s;
}

static float drift_noise(uint32_t *seed, float scale) {
    *seed = (*seed * 1664525u) + 1013904223u;
    float r = ((float)(*seed & 0xFFFFFF)) / (float)0xFFFFFF;
    return (r - 0.5f) * scale;
}

static inline float clamp_f(float v, float lo, float hi) {
    return v < lo ? lo : (v > hi ? hi : v);
}
static inline float ema_f(float nv, float ov, float a) {
    return a * nv + (1.0f - a) * ov;
}
static inline float delta_norm(float c, float b, float md) {
    return clamp_f((c - b) / (md + 1e-6f), 0.0f, 1.0f);
}
static inline float lerp(float a, float b, float t) {
    return a + t * (b - a);
}

/* SECTION 2: EXTENDED STRUCTS */

typedef struct {
    float heart_rate_bpm;
    float systolic_bp;
    float diastolic_bp;
    float hrv_rmssd_ms;
    float voice_pitch_hz;
    float voice_energy_db;
    float voice_tempo_wpm;
    float voice_tremor;
    float voice_valence;
    float text_sentiment;
    float text_arousal;
    float text_certainty;
    float typing_speed_cpm;
    float typing_pause_ratio;
    float backspace_rate;
    float sensor_confidence;
    float baseline_hr;
    float baseline_hrv;
    float baseline_pitch;
    float baseline_tempo;
    float baseline_typing_speed;
} SensorInputV2;

typedef struct {
    float virtual_heart_rate;
    float virtual_blood_pressure;
    float virtual_hrv;
    float virtual_cortisol;
    float virtual_adrenaline;
    float virtual_dopamine;
    float virtual_serotonin;
    float virtual_oxytocin;
    float virtual_norepinephrine;
    float virtual_muscle_tension;
    float virtual_breathing_rate;
    float virtual_gsr;
    float felt_anxiety;
    float felt_urgency;
    float felt_warmth;
    float felt_exhaustion;
    float felt_alertness;
    float felt_trust;
    float felt_connection;
    float felt_loneliness;
    float felt_safety;
    float felt_tension;
    float felt_energy;
    float confidence;
    float noise_seed_float;
    uint32_t _noise_seed;
} VirtualBodyV2;

typedef struct {
    float trust_level;
    float trust_velocity;
    int   betrayal_count;
    float trust_recovery_rate;
    float bond_strength;
    float bond_decay_rate;
    float shared_experience_score;
    int   interaction_count;
    float emotional_baseline_shift;
    float trauma_residue;
    float joy_reservoir;
    float emotional_inertia;
    int   phase;
} SocialEmotionalState;

void init_social_state(SocialEmotionalState *s) {
    memset(s, 0, sizeof(SocialEmotionalState));
    s->trust_level          = 0.10f;
    s->trust_recovery_rate  = 0.30f;
    s->bond_decay_rate      = 0.001f;
    s->emotional_inertia    = 0.40f;
    s->phase                = 0;
}

void update_relationship_phase(SocialEmotionalState *s) {
    float score = (s->trust_level * 0.4f)
                + (s->bond_strength * 0.4f)
                + clamp_f((float)s->interaction_count / 50.0f, 0.0f, 1.0f) * 0.2f;

    if      (score < 0.10f) s->phase = 0;
    else if (score < 0.25f) s->phase = 1;
    else if (score < 0.45f) s->phase = 2;
    else if (score < 0.65f) s->phase = 3;
    else if (score < 0.85f) s->phase = 4;
    else                    s->phase = 5;
}

void update_trust(SocialEmotionalState *soc,
                  const VirtualBodyV2 *body,
                  float interaction_quality,
                  float dt)
{
    float trust_delta;
    if (interaction_quality >= 0.0f) {
        trust_delta = interaction_quality
                    * 0.03f
                    * (1.0f - soc->trust_level)
                    * dt;
    } else {
        float betrayal_amp = 1.0f + (float)soc->betrayal_count * 0.2f;
        trust_delta = interaction_quality * 0.08f * betrayal_amp * dt;
        if (interaction_quality < -0.5f) {
            soc->betrayal_count++;
        }
    }

    soc->trust_velocity = trust_delta / (dt + 1e-6f);
    soc->trust_level    = clamp_f(soc->trust_level + trust_delta, 0.0f, 1.0f);
}

void update_bonding(SocialEmotionalState *soc, float dt,
                    float session_warmth_avg) {
    float bond_gain = session_warmth_avg * 0.02f * soc->trust_level * dt;
    soc->shared_experience_score += bond_gain;
    soc->bond_strength = clamp_f(
        soc->bond_strength + bond_gain - soc->bond_decay_rate * dt,
        0.0f, 1.0f
    );
    soc->interaction_count++;
    update_relationship_phase(soc);
}

void fuse_sensors_v2(const SensorInputV2 *in,
                     VirtualBodyV2 *body,
                     const SocialEmotionalState *soc)
{
    float hr_norm    = delta_norm(in->heart_rate_bpm, in->baseline_hr, 60.0f);
    float map_cur    = (in->systolic_bp + 2.0f * in->diastolic_bp) / 3.0f;
    float bp_norm    = clamp_f((map_cur - 93.0f) / 40.0f, 0.0f, 1.0f);
    float hrv_stress = 1.0f - clamp_f(
        (in->hrv_rmssd_ms - 20.0f) / (in->baseline_hrv - 20.0f + 1e-6f),
        0.0f, 1.0f);

    float pitch_d  = delta_norm(in->voice_pitch_hz,  in->baseline_pitch, 80.0f);
    float tempo_d  = delta_norm(in->voice_tempo_wpm, in->baseline_tempo, 80.0f);
    float energy_n = clamp_f((in->voice_energy_db + 60.0f) / 60.0f, 0.0f, 1.0f);
    float tremor_n = clamp_f(in->voice_tremor, 0.0f, 1.0f);
    float valence_n = (in->voice_valence + 1.0f) / 2.0f;

    float text_stress = clamp_f(
        (-in->text_sentiment + 1.0f) / 2.0f
        * in->text_arousal,
        0.0f, 1.0f
    );
    float text_positivity = clamp_f(
        (in->text_sentiment + 1.0f) / 2.0f * (1.0f - in->text_arousal * 0.3f),
        0.0f, 1.0f
    );
    float text_uncertainty = 1.0f - clamp_f(in->text_certainty, 0.0f, 1.0f);

    float typing_speed_n   = delta_norm(in->typing_speed_cpm,
                                        in->baseline_typing_speed, 100.0f);
    float pause_stress     = clamp_f(in->typing_pause_ratio * 1.5f, 0.0f, 1.0f);
    float backspace_stress = clamp_f(in->backspace_rate / 20.0f, 0.0f, 1.0f);

    float conf = clamp_f(in->sensor_confidence, 0.0f, 1.0f);
    hr_norm    = lerp(0.0f, hr_norm,    conf);
    bp_norm    = lerp(0.0f, bp_norm,    conf);
    hrv_stress = lerp(0.3f, hrv_stress, conf);
    tremor_n   = lerp(0.0f, tremor_n,   conf);
    text_stress = lerp(0.0f, text_stress, conf);

    body->confidence = conf;
    body->virtual_heart_rate     = ema_f(hr_norm, body->virtual_heart_rate,    0.30f);
    body->virtual_blood_pressure = ema_f(bp_norm, body->virtual_blood_pressure, 0.25f);
    body->virtual_hrv            = ema_f(1.0f - hrv_stress, body->virtual_hrv, 0.20f);

    float cort = (0.25f * hr_norm)
               + (0.25f * hrv_stress)
               + (0.15f * tremor_n)
               + (0.15f * text_stress)
               + (0.10f * pause_stress)
               + (0.10f * text_uncertainty);
    body->virtual_cortisol = ema_f(clamp_f(cort,0,1), body->virtual_cortisol, 0.12f);

    float adre = (0.30f * hr_norm)
               + (0.25f * bp_norm)
               + (0.20f * tempo_d)
               + (0.15f * backspace_stress)
               + (0.10f * energy_n);
    body->virtual_adrenaline = ema_f(clamp_f(adre,0,1), body->virtual_adrenaline, 0.45f);

    float norep = (0.40f * clamp_f(typing_speed_n, 0,1))
                + (0.35f * in->text_arousal)
                + (0.25f * (1.0f - pause_stress));
    body->virtual_norepinephrine = ema_f(clamp_f(norep,0,1),
                                         body->virtual_norepinephrine, 0.35f);

    float trust_gate = 0.5f + soc->trust_level * 0.5f;
    float dopa = ((0.35f * text_positivity)
               + (0.30f * valence_n)
               + (0.20f * (1.0f - body->virtual_cortisol))
               + (0.15f * energy_n)) * trust_gate;
    body->virtual_dopamine = ema_f(clamp_f(dopa,0,1), body->virtual_dopamine, 0.25f);

    float sero = 1.0f - (0.55f * body->virtual_cortisol
                       + 0.25f * body->virtual_adrenaline
                       + 0.20f * (1.0f - text_positivity));
    body->virtual_serotonin = ema_f(clamp_f(sero,0,1), body->virtual_serotonin, 0.08f);

    float oxt = (0.40f * soc->trust_level)
              + (0.35f * soc->bond_strength)
              + (0.25f * valence_n * (1.0f - body->virtual_cortisol));
    body->virtual_oxytocin = ema_f(clamp_f(oxt,0,1), body->virtual_oxytocin, 0.05f);

    body->virtual_muscle_tension = clamp_f(
        0.45f * body->virtual_adrenaline + 0.45f * body->virtual_cortisol
        + 0.10f * backspace_stress, 0,1);
    body->virtual_breathing_rate = clamp_f(
        0.50f * body->virtual_adrenaline + 0.35f * hr_norm
        + 0.15f * pause_stress, 0,1);
    body->virtual_gsr = ema_f(
        clamp_f(0.65f*body->virtual_adrenaline + 0.35f*tremor_n, 0,1),
        body->virtual_gsr, 0.5f);

    float noise_scale = 0.018f;
    body->virtual_cortisol       = clamp_f(body->virtual_cortisol
        + gaussian_noise(0, noise_scale * (1.0f + body->virtual_cortisol)), 0,1);
    body->virtual_adrenaline     = clamp_f(body->virtual_adrenaline
        + gaussian_noise(0, noise_scale * 1.5f), 0,1);
    body->virtual_dopamine       = clamp_f(body->virtual_dopamine
        + gaussian_noise(0, noise_scale * 0.8f), 0,1);
    body->virtual_serotonin      = clamp_f(body->virtual_serotonin
        + gaussian_noise(0, noise_scale * 0.4f), 0,1);
    body->virtual_oxytocin       = clamp_f(body->virtual_oxytocin
        + gaussian_noise(0, noise_scale * 0.6f), 0,1);

    float drift = drift_noise(&body->_noise_seed, 0.008f);
    body->virtual_serotonin = clamp_f(body->virtual_serotonin + drift, 0.0f, 1.0f);
}

void compute_felt_v2(VirtualBodyV2 *body,
                     const SocialEmotionalState *soc)
{
    body->felt_anxiety = clamp_f(
        0.35f * body->virtual_cortisol
      + 0.30f * body->virtual_adrenaline
      + 0.20f * (1.0f - body->virtual_serotonin)
      + 0.15f * (1.0f - soc->trust_level),
        0,1);

    body->felt_urgency = clamp_f(
        0.50f * body->virtual_adrenaline
      + 0.25f * body->virtual_heart_rate
      + 0.15f * body->virtual_norepinephrine
      + 0.10f * body->virtual_blood_pressure,
        0,1);

    body->felt_warmth = clamp_f(
        0.35f * body->virtual_dopamine
      + 0.35f * body->virtual_serotonin
      + 0.30f * body->virtual_oxytocin,
        0,1);

    body->felt_exhaustion = clamp_f(
        0.55f * body->virtual_cortisol
      + 0.25f * body->virtual_muscle_tension
      + 0.20f * (1.0f - body->virtual_hrv),
        0,1);

    body->felt_alertness = clamp_f(
        0.40f * body->virtual_norepinephrine
      + 0.30f * body->virtual_adrenaline
      + 0.20f * body->virtual_dopamine
      + 0.10f * body->virtual_heart_rate,
        0,1);

    body->felt_trust = clamp_f(
        0.55f * soc->trust_level
      + 0.30f * body->virtual_oxytocin
      + 0.15f * soc->bond_strength,
        0,1);

    body->felt_connection = clamp_f(
        0.40f * soc->bond_strength
      + 0.35f * body->virtual_oxytocin
      + 0.25f * body->felt_warmth,
        0,1);

    body->felt_loneliness = clamp_f(
        (1.0f - body->felt_connection) * 0.6f
      + body->virtual_cortisol * 0.4f
      - soc->bond_strength * 0.3f,
        0,1);

    body->felt_safety = clamp_f(
        0.35f * soc->trust_level
      + 0.30f * body->virtual_serotonin
      + 0.20f * body->virtual_oxytocin
      - 0.15f * body->virtual_adrenaline
      - 0.20f * body->virtual_cortisol
      + 0.20f,
        0,1);

    body->felt_tension = clamp_f(
        0.50f * body->virtual_muscle_tension
      + 0.30f * body->felt_anxiety
      + 0.20f * body->virtual_adrenaline,
        0,1);

    body->felt_energy = clamp_f(
        0.40f * body->virtual_dopamine
      + 0.35f * body->virtual_serotonin
      + 0.25f * (1.0f - body->felt_exhaustion),
        0,1);

    float inertia = soc->emotional_inertia * soc->bond_strength;
    body->felt_anxiety    = lerp(body->felt_anxiety,    0.5f, inertia * 0.1f);
    body->felt_urgency    = lerp(body->felt_urgency,    0.5f, inertia * 0.08f);
}

void apply_homeostasis_v2(VirtualBodyV2 *body,
                           const SocialEmotionalState *soc,
                           float dt)
{
    float cortisol_baseline = 0.05f
        + soc->trauma_residue    * 0.25f
        - soc->joy_reservoir     * 0.05f;

    float serotonin_baseline = 0.65f
        + soc->joy_reservoir     * 0.20f
        - soc->trauma_residue    * 0.15f
        + soc->bond_strength     * 0.10f;

    float oxytocin_baseline = 0.10f
        + soc->bond_strength     * 0.40f
        + soc->trust_level       * 0.20f;

    float dopamine_baseline = 0.45f
        + soc->joy_reservoir     * 0.15f
        - soc->trauma_residue    * 0.10f;

    struct { float *field; float target; float rate; } decays[] = {
        { &body->virtual_heart_rate,      0.10f,                   0.08f },
        { &body->virtual_blood_pressure,  0.10f,                   0.05f },
        { &body->virtual_hrv,             0.70f,                   0.06f },
        { &body->virtual_cortisol,        cortisol_baseline,       0.02f },
        { &body->virtual_adrenaline,      0.00f,                   0.14f },
        { &body->virtual_dopamine,        dopamine_baseline,       0.04f },
        { &body->virtual_serotonin,       serotonin_baseline,      0.008f},
        { &body->virtual_oxytocin,        oxytocin_baseline,       0.015f},
        { &body->virtual_norepinephrine,  0.05f,                   0.10f },
        { &body->virtual_muscle_tension,  0.05f + soc->trauma_residue*0.15f, 0.07f },
        { &body->virtual_breathing_rate,  0.15f,                   0.09f },
        { &body->virtual_gsr,             0.05f,                   0.11f },
    };

    int n = sizeof(decays) / sizeof(decays[0]);
    for (int i = 0; i < n; i++) {
        float d = (decays[i].target - *decays[i].field) * decays[i].rate * dt;
        *decays[i].field = clamp_f(*decays[i].field + d, 0.0f, 1.0f);
    }
}

#define PERSIST_MAGIC   0xA1B2C3D4
#define PERSIST_VERSION 2

typedef struct {
    uint32_t           magic;
    uint32_t           version;
    time_t             last_saved;
    VirtualBodyV2      body;
    SocialEmotionalState social;
    float              session_warmth_accumulator;
    uint32_t           total_ticks;
} PersistenceBlock;

int save_state(const char *path,
               const VirtualBodyV2 *body,
               const SocialEmotionalState *soc,
               float warmth_acc,
               uint32_t ticks)
{
    PersistenceBlock blk;
    blk.magic                    = PERSIST_MAGIC;
    blk.version                  = PERSIST_VERSION;
    blk.last_saved               = time(NULL);
    blk.body                     = *body;
    blk.social                   = *soc;
    blk.session_warmth_accumulator = warmth_acc;
    blk.total_ticks              = ticks;

    FILE *f = fopen(path, "wb");
    if (!f) return -1;
    fwrite(&blk, sizeof(PersistenceBlock), 1, f);
    fclose(f);
    return 0;
}

int load_state(const char *path,
               VirtualBodyV2 *body,
               SocialEmotionalState *soc,
               float *warmth_acc,
               uint32_t *ticks)
{
    FILE *f = fopen(path, "rb");
    if (!f) return -1;

    PersistenceBlock blk;
    size_t n = fread(&blk, sizeof(PersistenceBlock), 1, f);
    fclose(f);

    if (n != 1 || blk.magic != PERSIST_MAGIC || blk.version != PERSIST_VERSION)
        return -2;

    time_t now     = time(NULL);
    double gap_sec = difftime(now, blk.last_saved);
    float  gap_hrs = (float)(gap_sec / 3600.0);

    blk.social.bond_strength = clamp_f(
        blk.social.bond_strength - blk.social.bond_decay_rate * gap_hrs,
        0.0f, 1.0f
    );
    float sleep_cortisol_decay = clamp_f(gap_hrs * 0.03f, 0.0f, 0.4f);
    blk.body.virtual_cortisol = clamp_f(
        blk.body.virtual_cortisol - sleep_cortisol_decay, 0.0f, 1.0f
    );
    float sleep_serotonin_restore = clamp_f(gap_hrs * 0.01f, 0.0f, 0.2f);
    blk.body.virtual_serotonin = clamp_f(
        blk.body.virtual_serotonin + sleep_serotonin_restore, 0.0f, 1.0f
    );

    *body       = blk.body;
    *soc        = blk.social;
    *warmth_acc = blk.session_warmth_accumulator;
    *ticks      = blk.total_ticks;
    return 0;
}
