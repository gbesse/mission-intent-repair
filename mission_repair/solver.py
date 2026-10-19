"""Integer, discrete-time model. No flight hardware or orbital dynamics are implied."""

from copy import deepcopy
import hashlib
import json

from ortools.sat.python import cp_model


def validate(case):
    if not isinstance(case, dict):
        raise ValueError("invalid_case")
    h = case.get("horizon")
    if type(h) is not int or not 1 <= h <= 96:
        raise ValueError("invalid_horizon")
    if type(case.get("freeze_before", 0)) is not int or not 0 <= case.get("freeze_before", 0) <= h:
        raise ValueError("invalid_freeze")
    tasks = case.get("tasks", [])
    if not isinstance(tasks, list) or not tasks or len(tasks) > 30 or any(not isinstance(t, dict) for t in tasks):
        raise ValueError("invalid_tasks")
    ids = [t.get("id") for t in tasks]
    if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError("invalid_ids")
    for key in ("battery_capacity", "battery_initial", "storage_capacity", "storage_initial"):
        if type(case.get(key)) is not int or not 0 <= case[key] <= 1_000_000:
            raise ValueError("invalid_resource")
    if case["battery_initial"] > case["battery_capacity"] or case["storage_initial"] > case["storage_capacity"]:
        raise ValueError("invalid_initial")
    for key in ("solar", "baseline"):
        if not isinstance(case.get(key), list) or len(case[key]) != h or any(type(v) is not int or not 0 <= v <= 1_000_000 for v in case[key]):
            raise ValueError("invalid_profile")
    for t in tasks:
        if type(t.get("duration")) is not int or not 1 <= t["duration"] <= h:
            raise ValueError("invalid_duration")
        for key in ("energy", "value"):
            if type(t.get(key, 0)) is not int or not 0 <= t.get(key, 0) <= 1_000_000:
                raise ValueError("invalid_task_resource")
        if type(t.get("data_delta", 0)) is not int or abs(t.get("data_delta", 0)) > 1_000_000:
            raise ValueError("invalid_task_resource")
        if not isinstance(t.get("after", []), list) or any(not isinstance(d, str) for d in t.get("after", [])):
            raise ValueError("invalid_dependency")
        if any(d not in ids or d == t["id"] for d in t.get("after", [])):
            raise ValueError("invalid_dependency")
        if not isinstance(t.get("windows", []), list) or any(not isinstance(w, list) or len(w) != 2 or any(type(x) is not int for x in w)
               or not 0 <= w[0] <= w[1] <= h for w in t.get("windows", [])):
            raise ValueError("invalid_window")
        if not isinstance(t.get("channels", []), list) or not all(isinstance(x, str) for x in t.get("channels", [])):
            raise ValueError("invalid_channel")
    previous = case.get("previous", {})
    if not isinstance(previous, dict) or any(k not in ids or type(v) is not int or v < 0 or v >= h for k, v in previous.items()):
        raise ValueError("invalid_previous")
    return h, {t["id"]: t for t in tasks}


def legal_starts(case, task):
    duration = task["duration"]
    previous = case.get("previous", {})
    freeze = case.get("freeze_before", 0)
    frozen = task["id"] in previous and previous[task["id"]] < freeze
    starts = sorted({s for a, b in task.get("windows", [[0, case["horizon"]]])
                     for s in range(a, b - duration + 1)})
    return [s for s in starts if s == previous[task["id"]]] if frozen else [s for s in starts if s >= freeze]


def check_plan(case, plan):
    """Independent replay, deliberately without CP-SAT variables or solver output."""
    h, tasks = validate(case)
    if not isinstance(plan, dict):
        raise ValueError("invalid_plan")
    errors = []
    battery = case["battery_initial"]
    storage = case["storage_initial"]
    trace = [{"tick": 0, "battery": battery, "storage": storage}]
    for key, start in plan.items():
        if key not in tasks or type(start) is not int:
            errors.append({"code": "unknown_task", "task": key})
        elif start not in legal_starts(case, tasks[key]):
            errors.append({"code": "outside_window", "task": key})
    for key, task in tasks.items():
        previous = case.get("previous", {}).get(key)
        if task.get("required") and key not in plan:
            errors.append({"code": "required_missing", "task": key})
        if previous is not None and previous < case.get("freeze_before", 0) and plan.get(key) != previous:
            errors.append({"code": "frozen_changed", "task": key})
        if key in plan:
            for dep in task.get("after", []):
                if dep not in plan or plan[dep] + tasks[dep]["duration"] > plan[key]:
                    errors.append({"code": "dependency", "task": key, "dependency": dep})
    usable = {k: s for k, s in plan.items() if k in tasks and type(s) is int and 0 <= s < h}
    for tick in range(h):
        active = [tasks[k] for k, s in usable.items() if s <= tick < s + tasks[k]["duration"]]
        channels = [c for t in active for c in set(t.get("channels", []))]
        if len(channels) != len(set(channels)):
            errors.append({"code": "channel_collision", "tick": tick})
        battery = min(case["battery_capacity"], battery + case["solar"][tick]
                      - case["baseline"][tick] - sum(t.get("energy", 0) for t in active))
        storage += sum(tasks[k].get("data_delta", 0) for k, s in usable.items()
                       if s + tasks[k]["duration"] == tick + 1)
        if battery < 0:
            errors.append({"code": "battery_depleted", "tick": tick + 1})
        if not 0 <= storage <= case["storage_capacity"]:
            errors.append({"code": "storage_bounds", "tick": tick + 1})
        trace.append({"tick": tick + 1, "battery": battery, "storage": storage})
    return {"valid": not errors, "errors": errors, "trace": trace,
            "utility": sum(tasks[k].get("value", 0) for k in usable)}


def repair(case, seconds=5):
    h, tasks = validate(case)
    model = cp_model.CpModel()
    starts = {k: {s: model.new_bool_var(f"{k}@{s}") for s in legal_starts(case, t)} for k, t in tasks.items()}
    chosen = {k: model.new_bool_var(f"chosen:{k}") for k in tasks}
    assumptions = {}
    for key, task in tasks.items():
        model.add(sum(starts[key].values()) == chosen[key])
        if task.get("required"):
            a = model.new_bool_var(f"required:{key}")
            model.add(chosen[key] == 1).only_enforce_if(a)
            model.add_assumption(a)
            assumptions[a.index] = key
        previous = case.get("previous", {}).get(key)
        if previous is not None and previous < case.get("freeze_before", 0):
            model.add(chosen[key] == 1)
        for dep in task.get("after", []):
            model.add(chosen[key] <= chosen[dep])
            for s, x in starts[key].items():
                model.add(x <= sum(v for d, v in starts[dep].items() if d + tasks[dep]["duration"] <= s))
    channels = {c for t in tasks.values() for c in t.get("channels", [])}
    battery = [model.new_int_var(0, case["battery_capacity"], f"battery:{t}") for t in range(h + 1)]
    storage = [model.new_int_var(0, case["storage_capacity"], f"storage:{t}") for t in range(h + 1)]
    model.add(battery[0] == case["battery_initial"])
    model.add(storage[0] == case["storage_initial"])
    for tick in range(h):
        active = [(key, x) for key, choices in starts.items() for s, x in choices.items()
                  if s <= tick < s + tasks[key]["duration"]]
        for channel in channels:
            model.add(sum(x for key, x in active if channel in tasks[key].get("channels", [])) <= 1)
        spill = model.new_int_var(0, case["solar"][tick], f"spill:{tick}")
        model.add(battery[tick + 1] == battery[tick] + case["solar"][tick] - case["baseline"][tick]
                  - sum(tasks[key].get("energy", 0) * x for key, x in active) - spill)
        model.add(storage[tick + 1] == storage[tick] + sum(
            tasks[key].get("data_delta", 0) * x for key, choices in starts.items()
            for s, x in choices.items() if s + tasks[key]["duration"] == tick + 1))
    utility = sum(t.get("value", 0) * chosen[k] for k, t in tasks.items())
    previous = case.get("previous", {})
    changed = sum(1 - starts[k].get(previous[k], 0) if k in previous else chosen[k] for k in tasks)
    displacement = sum(abs(s - previous[k]) * x for k in previous for s, x in starts[k].items())
    edits = 3000 * changed + displacement
    model.maximize(utility)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = min(20, max(0.01, seconds))
    solver.parameters.num_search_workers = 1
    status = solver.solve(model)
    first_status = solver.status_name(status)
    digest = hashlib.sha256(json.dumps(case, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {"status": first_status, "input_sha256": digest, "plan": None,
                "required_conflict": [assumptions[i] for i in solver.sufficient_assumptions_for_infeasibility()
                                      if i in assumptions] if status == cp_model.INFEASIBLE else [],
                "conflict_is_minimal": False}
    best_plan = {k: s for k, choices in starts.items() for s, x in choices.items() if solver.value(x)}
    best_utility = sum(tasks[k].get("value", 0) for k in best_plan)
    utility_proven = status == cp_model.OPTIMAL
    edit_proven = False
    if utility_proven:
        model.add(utility == best_utility)
        model.minimize(edits)
        status = solver.solve(model)
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            best_plan = {k: s for k, choices in starts.items() for s, x in choices.items() if solver.value(x)}
            edit_proven = status == cp_model.OPTIMAL
    replay = check_plan(case, best_plan)
    if not replay["valid"]:
        raise RuntimeError("independent_replay_failed")
    changes = [{"task": k, "before": previous.get(k), "after": best_plan.get(k)}
               for k in tasks if previous.get(k) != best_plan.get(k)]
    return {"status": "OPTIMAL" if utility_proven and edit_proven else "FEASIBLE", "plan": best_plan,
            "input_sha256": digest, "utility_proven": utility_proven, "repair_proven": edit_proven,
            "utility": best_utility, "changes": changes, "replay": replay,
            "edit_cost": 3000 * len(changes) + sum(abs(best_plan[k] - previous[k])
                        for k in previous if k in best_plan)}


def contingency(case, blocked_tasks=(), battery_capacity=None):
    result = deepcopy(case)
    for task in result["tasks"]:
        if task["id"] in blocked_tasks:
            task["windows"] = []
    if battery_capacity is not None:
        result["battery_capacity"] = battery_capacity
    return result
