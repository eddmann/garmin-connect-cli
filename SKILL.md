---
name: garmin-connect
description: Query Garmin Connect fitness and health data including activities, athlete stats, sleep, heart rate, stress, and body battery. Use when the user asks about Garmin data, workouts, training, or health metrics.
---

# Garmin Connect CLI Skill

Query and manage Garmin Connect data via the `garmin-connect` CLI.

## Prerequisites

- Install CLI: `curl -fsSL https://raw.githubusercontent.com/eddmann/garmin-connect-cli/main/install.sh | sh`
- Authenticate: `garmin-connect auth login` (email/password, supports MFA)

## Quick Context

Get aggregated data in one call:

```bash
garmin-connect context                      # Full context: profile, stats, health, activities
garmin-connect context --activities 10      # More recent activities
garmin-connect context --focus stats,health # Specific sections only
```

## Commands

Run `garmin-connect --help` or `garmin-connect <command> --help` to discover all options.

### Activities

```bash
garmin-connect activities list [--after DATE] [--before DATE] [--limit N] [--type TYPE]
garmin-connect activities get <ID> [--details]
garmin-connect activities splits <ID>
garmin-connect activities download <ID> [--format TCX|GPX|FIT] [-o FILE]
garmin-connect activities upload <FILE>
garmin-connect activities delete <ID> [--force]
```

### Athlete

```bash
garmin-connect athlete              # Profile
garmin-connect athlete stats        # Daily statistics
garmin-connect athlete summary      # Comprehensive stats + body metrics
```

### Health

```bash
garmin-connect health sleep [--date DATE]
garmin-connect health heart-rate [--date DATE]
garmin-connect health steps [--date DATE]
garmin-connect health stress [--date DATE]
garmin-connect health body-battery [--date DATE]
garmin-connect health rhr [--date DATE]
```

`health sleep` returns a large object with per-epoch detail arrays. For a summary use:

```bash
garmin-connect health sleep [--date DATE] | jq '{
  date: .dailySleepDTO.calendarDate,
  total_h: (.dailySleepDTO.sleepTimeSeconds / 3600 | . * 10 | round / 10),
  score: .dailySleepDTO.sleepScores.overall.value,
  deep_pct: .dailySleepDTO.sleepScores.deepPercentage.value,
  rem_pct: .dailySleepDTO.sleepScores.remPercentage.value,
  light_pct: .dailySleepDTO.sleepScores.lightPercentage.value,
  avg_spo2: .dailySleepDTO.averageSpO2Value,
  lowest_spo2: .dailySleepDTO.lowestSpO2Value,
  avg_resp: .dailySleepDTO.averageRespirationValue,
  avg_stress: .dailySleepDTO.avgSleepStress,
  hrv: .avgOvernightHrv,
  hrv_status: .hrvStatus,
  body_battery: .bodyBatteryChange,
  feedback: .dailySleepDTO.sleepScoreFeedback
}'
```

For history over multiple days:

```bash
for date in 2026-05-29 2026-05-28 2026-05-27; do
  garmin-connect health sleep --date $date | jq '{
    date: .dailySleepDTO.calendarDate,
    total_h: (.dailySleepDTO.sleepTimeSeconds / 3600 | . * 10 | round / 10),
    score: .dailySleepDTO.sleepScores.overall.value,
    deep_pct: .dailySleepDTO.sleepScores.deepPercentage.value,
    rem_pct: .dailySleepDTO.sleepScores.remPercentage.value,
    avg_spo2: .dailySleepDTO.averageSpO2Value,
    lowest_spo2: .dailySleepDTO.lowestSpO2Value,
    hrv: .avgOvernightHrv,
    body_battery: .bodyBatteryChange
  }'
done
```

### Training

```bash
garmin-connect training status [--date DATE]     # Productive, Peaking, etc.
garmin-connect training readiness [--date DATE]  # Readiness score (0-100)
garmin-connect training vo2max [--date DATE]
garmin-connect training hrv [--date DATE]
garmin-connect training fitness-age
```

### Weight

```bash
garmin-connect weight list [--start DATE] [--end DATE]
garmin-connect weight get [--date DATE]
garmin-connect weight log <WEIGHT_KG> [--date DATE]
```

### Workouts

```bash
garmin-connect workouts list [--limit N]
garmin-connect workouts get <ID>
garmin-connect workouts create <FILE|-> [--examples]
garmin-connect workouts delete <ID> [--force]
garmin-connect workouts schedule <ID> <DATE>
garmin-connect workouts unschedule <SCHEDULED_ID> [--force]
garmin-connect workouts calendar [--year N] [--month N]
garmin-connect workouts download <ID> [-o FILE]
```

## Data Units

| Field                     | Unit    |
| ------------------------- | ------- |
| distance                  | meters  |
| duration, movingTime      | seconds |
| averageSpeed, maxSpeed    | m/s     |
| elevation                 | meters  |
| dates                     | ISO8601 |


## Filtering noise

1. Filter null values:
`garmin-connect health stress | jq 'with_entries(select(.value != null))'`

2. HRV — summary only, skip 100+ raw readings:
`garmin-connect training hrv | jq '.hrvSummary'`

3. Body battery — drop raw arrays and descriptors:
`garmin-connect health body-battery | jq 'del(.bodyBatteryValuesArray, .bodyBatteryValueDescriptorDTOList, .bodyBatteryActivityEvent)'`

4. Context — focus on what you need and strip nulls:
`garmin-connect context --focus health | jq 'del(.. | nulls)'`

5. Interval data — aggregate instead of listing raw points:
`garmin-connect health steps -d 2026-05-27 | jq '[.[].steps] | add'`

6. `255` (0xFF) is a Garmin sentinel meaning "no data". Filter before aggregating interval arrays:
`garmin-connect health sleep | jq '[.breathingDisruptionData[] | select(.value != 255) | .value] | {max: max, avg: (add / length | . * 10 | round / 10)}'`


## Creating and managing workouts

```bash
garmin-connect workouts list [--limit N]                 # list workout templates
garmin-connect workouts get <ID>                         # details of a template
garmin-connect workouts create <FILE|-|--examples>       # create from JSON file or stdin
garmin-connect workouts delete <ID> [--force]            # delete template
garmin-connect workouts schedule <ID> <DATE>             # schedule for a date (YYYY-MM-DD)
garmin-connect workouts unschedule <SCHEDULED_ID> [--force]  # remove from calendar
garmin-connect workouts calendar [--year N] [--month N]  # view monthly schedule
garmin-connect workouts download <ID> [-o FILE]          # download as .fit file
```

### Quick start

```bash
# See example JSON payloads (easy run, intervals, HR-zone run)
garmin-connect workouts create --examples

# Save an example and tweak it
garmin-connect workouts create --examples | grep -A 50 '"easy_run"' > run.json
$EDITOR run.json
garmin-connect workouts create run.json

# List, schedule, and verify
garmin-connect workouts list | jq '.[] | {id: .workoutId, name: .workoutName}'
garmin-connect workouts schedule <ID> 2026-06-10
garmin-connect workouts calendar --year 2026 --month 6
```

After creation the workout syncs to the device via Garmin Connect app
(Training → Workouts → Send to Device), or automatically on next sync.

### Pace conversions (min/km → m/s)

| Pace (min/km) | Speed (m/s) |
|---------------|-------------|
| 7:00 | 2.381 |
| 7:30 | 2.222 |
| 8:00 | 2.083 |
| 8:30 | 1.961 |
| 9:00 | 1.852 |
| 9:30 | 1.754 |
| 10:00 | 1.667 |
| 11:00 | 1.515 |

Formula: `speed = 1000 / (pace_min * 60)`

In pace zone targets: `targetValueOne` = faster end (higher m/s), `targetValueTwo` = slower end (lower m/s).

### Step types

| stepTypeId | stepTypeKey | Use |
|------------|-------------|-----|
| 1 | warmup | Warmup |
| 2 | cooldown | Cooldown |
| 3 | interval | Main work interval |
| 4 | recovery | Recovery between intervals |
| 5 | rest | Full stop rest |

### End condition types

| conditionTypeId | conditionTypeKey | Unit |
|----------------|-----------------|------|
| 1 | lap.button | Press lap button |
| 2 | time | Seconds |
| 3 | distance | Meters |
| 4 | calories | kcal |

### Target types

| workoutTargetTypeId | workoutTargetTypeKey | Notes |
|--------------------|---------------------|-------|
| 1 | no.target | No target |
| 4 | heart.rate.zone | targetValueOne/Two = bpm |
| 6 | pace.zone | targetValueOne/Two = m/s |

### Sport types

| sportTypeId | sportTypeKey |
|-------------|-------------|
| 1 | running |
| 2 | cycling |
| 5 | swimming |

## Ready-to-use recipes

### Sleep summary over N days

```bash
for date in 2026-05-29 2026-05-28 2026-05-27 2026-05-26 2026-05-25; do
  garmin-connect health sleep --date $date | jq '{
    date: .dailySleepDTO.calendarDate,
    total_h: (.dailySleepDTO.sleepTimeSeconds / 3600 | . * 10 | round / 10),
    score: .dailySleepDTO.sleepScores.overall.value,
    deep_pct: .dailySleepDTO.sleepScores.deepPercentage.value,
    rem_pct: .dailySleepDTO.sleepScores.remPercentage.value,
    avg_spo2: .dailySleepDTO.averageSpO2Value,
    lowest_spo2: .dailySleepDTO.lowestSpO2Value,
    hrv: .avgOvernightHrv,
    body_battery: .bodyBatteryChange
  }'
done
```

### Breathing and sleep apnea

```bash
garmin-connect health sleep [--date DATE] | jq '{
  disruption_severity: .dailySleepDTO.breathingDisruptionSeverity,
  disruption_max: ([.breathingDisruptionData[] | select(.value != 255) | .value] | max),
  disruption_avg: ([.breathingDisruptionData[] | select(.value != 255) | .value] | add / length | . * 10 | round / 10),
  resp_avg: .dailySleepDTO.averageRespirationValue,
  resp_low: .dailySleepDTO.lowestRespirationValue,
  resp_high: .dailySleepDTO.highestRespirationValue,
  spo2_avg: .dailySleepDTO.averageSpO2Value,
  spo2_low: .dailySleepDTO.lowestSpO2Value
}'
```

### Body battery: intraday pattern (Moscow time UTC+3)

```bash
garmin-connect health body-battery | jq '.[0].bodyBatteryValuesArray | map({
  time: (.[0] / 1000 + 10800 | strftime("%H:%M")),
  level: .[1]
})'
```

### Body battery: charged/drained over N days

```bash
for date in 2026-05-29 2026-05-28 2026-05-27; do
  garmin-connect health body-battery --date $date | jq --arg d "$date" '.[0] | {
    date: $d,
    charged: .charged,
    drained: .drained,
    net: (.charged - .drained)
  }'
done
```

### Resting heart rate: weekly trend

```bash
for date in 2026-05-29 2026-05-22 2026-05-15 2026-05-08 2026-05-01 2026-04-24 2026-04-17; do
  rhr=$(garmin-connect health heart-rate --date $date | jq '.restingHeartRate')
  echo "{\"date\": \"$date\", \"rhr\": $rhr}"
done
```

### Running activities: cadence, mechanics, HR zones

```bash
garmin-connect activities list --limit 30 | jq '[.[] | select(.activityType.typeKey == "running")] | .[] | {
  date: .startTimeLocal[:10],
  dist_km: (.distance / 1000 | . * 10 | round / 10),
  pace_min_km: (.duration / (.distance / 1000) / 60 | . * 10 | round / 10),
  avg_hr: .averageHR,
  cadence_spm: .averageRunningCadenceInStepsPerMinute,
  stride_m: .avgStrideLength,
  ground_contact_ms: .avgGroundContactTime,
  vertical_osc_cm: .avgVerticalOscillation,
  aerobic_te: .aerobicTrainingEffect,
  anaerobic_te: .anaerobicTrainingEffect,
  hr_zones_sec: {z1: .hrTimeInZone_1, z2: .hrTimeInZone_2, z3: .hrTimeInZone_3, z4: .hrTimeInZone_4, z5: .hrTimeInZone_5}
}'
```

### Strength training: load and HR zones

```bash
garmin-connect activities list --limit 30 | jq '[.[] | select(.activityType.typeKey == "strength_training")] | .[] | {
  date: .startTimeLocal[:10],
  duration_min: (.duration / 60 | round),
  avg_hr: .averageHR,
  max_hr: .maxHR,
  training_load: .activityTrainingLoad,
  aerobic_te: .aerobicTrainingEffect,
  anaerobic_te: .anaerobicTrainingEffect,
  hr_zones_sec: {z1: .hrTimeInZone_1, z2: .hrTimeInZone_2, z3: .hrTimeInZone_3, z4: .hrTimeInZone_4, z5: .hrTimeInZone_5}
}'
```

### Weight and body composition: history

```bash
garmin-connect weight list --start 2026-01-01 --end 2026-05-31 | jq '[.dailyWeightSummaries[] | .allWeightMetrics[] | {
  date: .calendarDate,
  weight_kg: (.weight / 1000),
  body_fat_pct: .bodyFat,
  muscle_kg: (if .muscleMass then .muscleMass / 1000 else null end)
}] | sort_by(.date)'
```

### Training readiness: summary

```bash
garmin-connect training readiness | jq '.[0] | {
  score: .score,
  level: .level,
  sleep_score: .sleepScore,
  hrv_factor: .hrvFactorPercent,
  recovery_time_h: .recoveryTime,
  acwr: .acwrFactorFeedback
}'
```

### HRV: summary only, without raw readings

```bash
garmin-connect training hrv | jq '.hrvSummary | {
  weekly_avg: .weeklyAvg,
  last_night_avg: .lastNightAvg,
  status: .status,
  baseline: .baseline
}'
```

### HRV: weekly trend over N weeks

```bash
for date in 2026-05-29 2026-05-22 2026-05-15 2026-05-08 2026-05-01 2026-04-24 2026-04-17 2026-04-10 2026-04-03; do
  garmin-connect training hrv --date $date | jq --arg d "$date" '{
    date: $d,
    last_night_avg: .hrvSummary.lastNightAvg,
    last_night_5min_high: .hrvSummary.lastNight5MinHigh,
    weekly_avg: .hrvSummary.weeklyAvg,
    status: .hrvSummary.status,
    baseline: {low: .hrvSummary.baseline.balancedLow, high: .hrvSummary.baseline.balancedUpper}
  }'
done
```

Interpreting HRV status (personal baseline ~51–66 ms):
- `weekly_avg < 50` + `RHR > 53` → overreaching signal, rest or easy only
- `weekly_avg 51–58` → normal, train as planned
- `weekly_avg 59–66` → optimal, good window to increase load
- `status: LOW` for 2+ consecutive weeks → investigate sleep, stress, volume

## Common Patterns

```bash
# Recent activities
garmin-connect activities list --limit 10

# This month's activities
garmin-connect activities list --after 2025-12-01

# Filter by type
garmin-connect activities list | jq '[.[] | select(.activityType.typeKey=="running")]'

# Total running distance
garmin-connect activities list --limit 50 | jq '[.[] | select(.activityType.typeKey=="running") | .distance] | add / 1000'
```

## Auth Status

```bash
garmin-connect auth status    # Check if authenticated
garmin-connect auth login     # Login with email/password (supports MFA)
garmin-connect auth logout    # Clear stored tokens
```

## Activity Types

running, cycling, swimming, walking, hiking, trail_running, open_water_swimming, indoor_cycling, virtual_cycling, strength_training, cardio, yoga, pilates, elliptical, indoor_rowing, other

## Exit Codes

- 0 = Success
- 1 = General error
- 2 = Auth error (run `garmin-connect auth login`)
