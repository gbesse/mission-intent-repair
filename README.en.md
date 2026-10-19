# Mission Intent Repair

[Français](README.md) · [Español](README.es.md)

**A link disappears. Which plan saves the most value without rewriting the past?**

An executable mission-repair lab using the real OR-Tools CP-SAT solver, a local interface, and an independent checker. Cut the demo's primary relay: the plan switches to its backup, preserves the two started tasks, and checks energy and storage at every tick.

![Synthetic demo: repair after losing a relay](docs/preview-fr.png)

## Try it

Python 3.11 or newer; no key or remote service.

```sh
python3 -m venv .venv
.venv/bin/pip install .
.venv/bin/python -m mission_repair serve --lang en
```

Open `http://127.0.0.1:8764/?lang=en`. Scenario, inputs, plan and JSON evidence stay local. The same interface supports FR/EN/ES.

```sh
.venv/bin/python -m mission_repair demo --lang en
.venv/bin/python -m mission_repair repair mission_repair/examples/lunar-relay.json
.venv/bin/python -m mission_repair check case.json plan.json
```

`check` accepts `{ "task-id": start_tick }` or a report containing `plan`. Error codes are stable; CLI messages use `--lang`.

## What it computes

- Start/end windows, integer durations, dependencies and exclusive channels.
- Battery with solar production, baseline consumption and task load; storage with production and downlink at task completion.
- A frozen past: tasks whose previous start precedes `freeze_before` retain that exact start, including tasks in progress.
- Lexicographic objective: maximize declared utility, then minimize changed tasks, then temporal displacement. The coefficient 3000 exceeds all possible displacement within the accepted limits.
- Independent replay: windows, requirements, dependencies, collisions, battery and storage are recalculated without solver variables.
- SHA-256 of the assumptions, explicit changes and replayable JSON export.

The supplied synthetic outage yields **8 declared utility units versus 10 before the outage**, with **two changed tasks**. These values come from the scenario; they are not measured spaceflight performance. The old plan becomes invalid after the outage.

`OPTIMAL` means all three objective levels are proven within the model. `FEASIBLE` means an independently checked plan exists without a complete optimality proof. `INFEASIBLE` denotes a model contradiction; `required_conflict` is a sufficient set of conflicting requirements, **not necessarily minimal**. `UNKNOWN` preserves the absence of a result.

## Model and limits

At most 30 tasks and 96 ticks; energy and data use arbitrary integers. Generation and consumption are aggregated per tick; simultaneous storage changes are aggregated at the boundary. A reduced capacity applies to the entire horizon: to model a fault at a specific time, supply a new horizon and its initial state instead of changing the past retroactively.

This prototype computes no orbits, attitude or visibility geometry. Users supply windows. No hardware, flight simulator or embedded software is connected; results do not qualify a real mission. Solver time is bounded and proofs concern only supplied assumptions. The server listens on loopback and exposes no flight-command endpoint.

## Ecosystem and comparison

[PlanDev](https://nasa-ammos.github.io/plandev-docs/introduction/) already provides mission modeling, scheduling and constraints. [OR-Tools](https://developers.google.com/optimization/scheduling/job_shop) already solves scheduling problems. This repository reuses CP-SAT and concentrates on a small standalone demonstration: **outage → frozen past → bounded optimal repair → independent replay**. No general superiority is claimed.

[Mission Benchmark Commons](https://github.com/gbesse/mission-benchmark-commons) compares orbital engines; [Contact Market](https://github.com/gbesse/contact-market) optimizes contacts. This project repairs schedules and resources after disruption; those repositories are not copied.

## Verification

```sh
.venv/bin/python -m unittest discover -s tests -v
npm ci
npx playwright install chromium
PYTHON=.venv/bin/python npm run test:browser
npm run format:check
```

Tests include exhaustive small-problem comparisons, outages, impossible requirements, depleted resources, frozen history and browser exports in all three languages. CI also installs a Python wheel outside the source tree. MIT license; research alpha.
