# How to trigger a detector

`StandardDetector` takes exposures in response to a trigger source. The source is
selected with `DetectorTrigger` and configured through `TriggerInfo`, which the
detector receives when a plan calls `prepare()`.

This article shows what each `TriggerInfo` permutation means, and how the detector
reacts to it.

## The permutations

The table below covers the common cases. `livetime` is the exposure time in seconds
and `deadtime` is the gap between exposures in seconds.

| TriggerInfo | Behaviour |
|-------------|-----------|
| `TriggerInfo()` | Internal triggering. The detector times its own exposures. Exposure and period are left at whatever the detector is currently set to. This is the default when a plan calls `trigger()` without `prepare()`. |
| `TriggerInfo(trigger=DetectorTrigger.EXTERNAL_EDGE, livetime=1.0)` | Exposure set to `1.0`. The period is set to `livetime + get_deadtime(livetime)` so frames follow back to back. |
| `TriggerInfo(trigger=DetectorTrigger.EXTERNAL_EDGE, livetime=1.0, deadtime=0.1)` | Exposure set to `1.0` and the gap set explicitly to `0.1`. |
| `TriggerInfo(number_of_events=0)` | Arm and keep going until disarmed. Only works if the detector supports it. |
| `TriggerInfo(number_of_events=100)` | Arm and take exactly 100 frames. |

## What happens on arm

When `prepare()` is called the detector logic works through the following.

1. The trigger mode signals are set to match the requested `DetectorTrigger`.
2. For `INTERNAL` or `EXTERNAL_EDGE` the exposure time is set to `livetime`. A value
   of `0` means leave whatever is currently set.
3. For `INTERNAL` the gap between exposures is set to `deadtime`. A value of `0`
   means use the shortest gap the detector supports.
4. For `EXTERNAL_EDGE` the gap is derived from `get_deadtime()` on the detector
   logic, which reads the detector's own configuration signals.
5. `num` sets how many frames to take. `0` means continuous acquisition until the
   detector is disarmed, any positive value arms for exactly that many frames.

## Worked examples

The canonical entry point is `prepare()` on the detector itself. Internal triggering
with 11 frames.

```python
detector = MyDetector("BL11I:DET:", path_provider)

await detector.prepare(TriggerInfo(number_of_events=11))
```

External edge triggering with a 1 ms exposure and 5 frames.

```python
await detector.prepare(
    TriggerInfo(
        trigger=DetectorTrigger.EXTERNAL_EDGE,
        number_of_events=5,
        livetime=0.001,
    )
)
```

## Choosing between edge and level triggering

`EXTERNAL_EDGE` starts one exposure per rising edge of the trigger input.
`EXTERNAL_LEVEL` starts an exposure on the rising edge and ends it on the falling
edge, so the trigger source controls the exposure length directly. If your hardware
gate signal already matches the exposure window you want, use `EXTERNAL_LEVEL`.

## Checking what a detector supports

Not every detector supports every trigger mode. Call `get_trigger_deadtime()` to see
the supported trigger types and the deadtime the detector reports.

```python
supported, deadtime = await detector.get_trigger_deadtime()
```

If a mode is missing from `supported` the detector cannot be prepared with it, and
`prepare()` will raise.
