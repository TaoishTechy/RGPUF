# Frame 5 — Semantic META-K Controller Demo
## `demo_05_meta_k_controller.py`

---

## 1. Core Purpose

Promote semantic mode from a **passive observer** to a **causal director** of the RGPUF system. In prior frames, semantic mode has been a diagnostic layer: it observes telemetry, labels outcomes, and possibly annotates failures. In Frame 5, semantic mode becomes an active controller — META-K — that:

1. **Observes** telemetry from all modes.
2. **Diagnoses** which mode is failing and why (using the mode grammars from Frame 4).
3. **Proposes repair** candidates from its policy library.
4. **Spends tokens** from the token economy to fund analysis and repairs.
5. **Activates law leases** to temporarily install repair laws in the target mode.
6. **Measures effect** by comparing PR_strict before and after the repair.
7. **Prunes or keeps** the repair based on measured impact.
8. **Mutates** the repair if partial success is detected.

The critical insight is that META-K's value is **not** measured by its own PR_strict (which may remain low since it doesn't directly control any physical agent). Instead, META-K is scored by its **causal impact on other modes**:

$$V_{\text{sem}} = \frac{\Delta PR_{\text{strict}}^{\text{cross}}}{\lambda \cdot C_{\text{analysis}} + \mu \cdot T_{\text{wasted}}}$$

Where:
- $\Delta PR_{\text{strict}}^{\text{cross}} = \sum_{m \neq \text{semantic}} \left( PR_{\text{strict}}^{m,\text{after}} - PR_{\text{strict}}^{m,\text{before}} \right)$ is the total improvement across all non-semantic modes attributable to META-K's interventions.
- $C_{\text{analysis}}$ is the computational cost of META-K's analysis (measured in token-equivalent units).
- $T_{\text{wasted}}$ is the number of tokens spent on repairs that did not improve PR_strict.
- $\lambda, \mu$ are weighting hyperparameters.

**Interpretation:** META-K scores only if it improves other modes. An idle META-K that spends nothing gets $V_{\text{sem}} = 0$ (undefined, treated as 0). A META-K that spends many tokens with no improvement gets $V_{\text{sem}} < 0$. A META-K that accurately diagnoses failures and proposes effective cheap repairs gets $V_{\text{sem}} > 0$.

---

## 2. Core Equation

### 2.1 Semantic Value

$$V_{\text{sem}} = \frac{\Delta PR_{\text{strict}}^{\text{cross}}}{\lambda \cdot C_{\text{analysis}} + \mu \cdot T_{\text{wasted}}}$$

**Expanded form:**

$$V_{\text{sem}} = \frac{\sum_{m \in \mathcal{M} \setminus \{\text{semantic}\}} \left( PR_{\text{strict}}^{m}(t_{\text{after}}) - PR_{\text{strict}}^{m}(t_{\text{before}}) \right)}{\lambda \cdot \sum_{r \in \mathcal{R}} C(r) + \mu \cdot \sum_{r \in \mathcal{R}_{\text{fail}}} T(r)}$$

Where:
- $\mathcal{M}$ is the set of all modes.
- $\mathcal{R}$ is the set of all repair events in the evaluation window.
- $\mathcal{R}_{\text{fail}} \subseteq \mathcal{R}$ is the set of repair events that did not improve PR_strict.
- $C(r)$ is the analysis cost of repair event $r$.
- $T(r)$ is the token cost of repair event $r$.

**Rolling variant (to prevent inflation from early lucky repairs):**

$$V_{\text{sem}}^{(k)} = \frac{\sum_{i=k-N+1}^{k} \Delta PR_{\text{strict}}^{\text{cross},(i)}}{\lambda \cdot \sum_{i=k-N+1}^{k} C^{(i)} + \mu \cdot \sum_{i=k-N+1}^{k} T_{\text{wasted}}^{(i)}}$$

Where $N$ is the rolling window size (default: 10 repairs).

**Bounds:**

- $V_{\text{sem}} \in (-\infty, +\infty)$.
- $V_{\text{sem}} = 0$ when no repairs are attempted (numerator = 0, denominator > 0, but we define $0/0 = 0$).
- $V_{\text{sem}} > 0$ indicates the controller is net helpful.
- $V_{\text{sem}} < 0$ indicates the controller is net harmful.

### 2.2 META-K Energy

META-K has an energy budget that limits how many repairs it can attempt per evaluation window:

$$E_{\text{meta-k}}(t) = E_{\text{meta-k}}(0) + \sum_{i=0}^{t} \Delta E_i$$

Where:
- $E_{\text{meta-k}}(0)$ is the initial energy allocation.
- $\Delta E_i = +\Delta_{\text{reward}}$ if repair $i$ succeeded (replenish some energy).
- $\Delta E_i = -C_{\text{repair}}(i)$ if repair $i$ was attempted (spend energy).

If $E_{\text{meta-k}} < E_{\text{min}}$, META-K enters a low-energy state where it can only observe, not repair.

---

## 3. META-K Control Loop

The META-K controller executes a 13-step loop every time it is activated (either on a fixed schedule or triggered by a failure detection event):

### Step 1: Read Telemetry

Gather the latest telemetry from all modes. This includes:

- Per-mode PR_strict, PR_risk, R_recover, E_recover.
- Terminal states, subterminal states, failure causes.
- Token balances per mode.
- Active law leases and their remaining durations.
- Recovery path status for any ongoing recoveries.

```python
def read_telemetry(all_mode_telemetry: Dict[str, dict]) -> dict:
    """
    Aggregates telemetry from all modes into a unified META-K view.
    Returns a structured dictionary with per-mode summaries and global metrics.
    """
    global_view = {
        "timestamp": datetime.utcnow().isoformat(),
        "modes": {},
        "global": {
            "total_token_balance": 0,
            "total_active_leases": 0,
            "cascade_probability": 0.0,
            "meta_k_energy": 0.0
        }
    }

    for mode_name, telemetry in all_mode_telemetry.items():
        global_view["modes"][mode_name] = {
            "pr_strict": telemetry.get("pr_strict", 0.0),
            "pr_risk": telemetry.get("pr_risk", 0.0),
            "r_recover": telemetry.get("R_recover", 1.0),
            "e_recover": telemetry.get("E_recover", 0.0),
            "terminal_state": telemetry.get("terminal_state", "unknown"),
            "subterminal_state": telemetry.get("subterminal_state"),
            "failure_cause": telemetry.get("failure_cause"),
            "token_balance": telemetry.get("token_balance", 0),
            "active_leases": telemetry.get("active_leases", []),
            "recovery_status": telemetry.get("recovery_status", "nominal"),
            "rtq": telemetry.get("RTQ", 0.0)
        }
        global_view["global"]["total_token_balance"] += telemetry.get("token_balance", 0)
        global_view["global"]["total_active_leases"] += len(telemetry.get("active_leases", []))

    return global_view
```

### Step 2: Detect Failure Class

Examine all mode telemetry to identify which modes are in failure states. Use the mode grammars from Frame 4 to classify failures.

```python
def detect_failure_class(global_view: dict, grammars: Dict[str, dict]) -> List[dict]:
    """
    Returns list of active failure events, sorted by severity.
    Each event: {mode, terminal, subterminal, cause, depth, severity}
    """
    failures = []
    for mode_name, mode_data in global_view["modes"].items():
        grammar = grammars[mode_name]
        if mode_data["terminal_state"] in grammar["failure_terminals"]:
            failures.append({
                "mode": mode_name,
                "terminal": mode_data["terminal_state"],
                "subterminal": mode_data["subterminal_state"],
                "cause": mode_data["failure_cause"],
                "depth": mode_data.get("failure_depth", 0),
                "severity": grammar["severity_map"].get(mode_data["terminal_state"], 0.5),
                "recoverable": grammar["recoverability_map"].get(mode_data["terminal_state"], False)
            })
    failures.sort(key=lambda f: f["severity"], reverse=True)
    return failures
```

### Step 3: Identify Mode Grammar

For each detected failure, retrieve the full mode grammar including terminal states, subterminal states, root causes, and recovery paths.

```python
def identify_mode_grammar(failures: List[dict], grammars: Dict[str, dict]) -> Dict[str, dict]:
    """
    Returns {mode: grammar} for all modes with active failures.
    """
    return {f["mode"]: grammars[f["mode"]] for f in failures}
```

### Step 4: Inspect Law Ecology

Examine the current law ecology for the failing mode. Determine which laws are active, which are leased, which are dormant, and how they interact.

```python
def inspect_law_ecology(mode: str, global_view: dict, law_registry: dict) -> dict:
    """
    Returns ecology snapshot for the failing mode:
      - active_laws: list of laws currently governing the mode
      - leased_laws: list of temporarily installed repair laws with remaining lease duration
      - dormant_laws: list of laws that were previously active but are currently inactive
      - dependency_graph: adjacency list of law interactions
      - conflict_map: pairs of laws that may conflict
    """
    mode_data = global_view["modes"][mode]
    active = law_registry["active"].get(mode, [])
    leased = mode_data.get("active_leases", [])
    dormant = law_registry["dormant"].get(mode, [])
    deps = law_registry["dependencies"].get(mode, {})
    conflicts = law_registry["conflicts"].get(mode, [])

    return {
        "active_laws": active,
        "leased_laws": leased,
        "dormant_laws": dormant,
        "dependency_graph": deps,
        "conflict_map": conflicts,
        "ecology_health": compute_ecology_health(active, leased, dormant, conflicts)
    }
```

### Step 5: Inspect Token Balance

Check whether META-K has sufficient tokens to fund analysis and a potential repair.

```python
def inspect_token_balance(
    global_view: dict,
    estimated_analysis_cost: float,
    estimated_repair_cost: float
) -> dict:
    """
    Returns {available, sufficient, deficit, recommendation}
    """
    balance = global_view["global"]["total_token_balance"]
    total_cost = estimated_analysis_cost + estimated_repair_cost
    sufficient = balance >= total_cost

    return {
        "available": balance,
        "required": total_cost,
        "sufficient": sufficient,
        "deficit": max(0, total_cost - balance),
        "recommendation": (
            "proceed" if sufficient
            else "defer" if balance >= estimated_analysis_cost
            else "observe_only"
        )
    }
```

### Step 6: Choose Repair Candidate

Based on the failure class, mode grammar, law ecology, and failure memory bank (from Frame 4, Enhancement 32), generate a list of repair candidates.

```python
def choose_repair_candidates(
    failure: dict,
    grammar: dict,
    ecology: dict,
    memory_bank: dict,
    policy_library: dict
) -> List[dict]:
    """
    Returns list of repair candidates with metadata:
      {name, policy, source, expected_delta_pr, semantic_confidence, cost_estimate, risk_estimate}
    """
    signature = f"{failure['mode']}.{failure['terminal']}.{failure['subterminal']}.{failure['cause']}"

    candidates = []

    # Source 1: Failure Memory Bank (proven macros)
    macro = memory_bank.lookup(signature)
    if macro:
        candidates.append({
            "name": macro["name"],
            "policy": macro["policy"],
            "source": "memory_bank",
            "expected_delta_pr": macro.get("expected_delta_pr", 0.1),
            "semantic_confidence": macro["success_rate"],
            "cost_estimate": macro.get("resource_cost_estimate", 1.0),
            "risk_estimate": 1.0 - macro["success_rate"],
            "provenance": "macro_v{}".format(macro.get("version", 1))
        })

    # Source 2: Policy Library (general policies for this failure class)
    failure_class = f"{failure['mode']}.{failure['terminal']}"
    for policy in policy_library.get(failure_class, []):
        candidates.append({
            "name": policy["name"],
            "policy": policy["policy_fn"],
            "source": "policy_library",
            "expected_delta_pr": policy["expected_delta_pr"],
            "semantic_confidence": policy["confidence"],
            "cost_estimate": policy["cost"],
            "risk_estimate": policy["risk"],
            "provenance": "policy_library_v{}".format(policy.get("version", 1))
        })

    # Source 3: Dormant law revival
    for dormant in ecology["dormant_laws"]:
        if dormant.get("addresses_failure", failure_class):
            candidates.append({
                "name": f"revive_{dormant['name']}",
                "policy": dormant["policy_fn"],
                "source": "dormant_revival",
                "expected_delta_pr": dormant.get("historical_delta_pr", 0.05),
                "semantic_confidence": 0.5,  # uncertain, was dormant for a reason
                "cost_estimate": dormant.get("cost", 0.5),
                "risk_estimate": dormant.get("risk", 0.3),
                "provenance": "dormant_revival"
            })

    # Source 4: Cross-mode porting (from Enhancement 36)
    cross_mode_candidates = find_cross_mode_repairs(failure, policy_library)
    candidates.extend(cross_mode_candidates)

    return candidates
```

### Step 7: Run Repair Auction

Score each candidate using a multi-objective ranking (from Enhancement 37) and select the winner.

```python
def run_repair_auction(
    candidates: List[dict],
    auction_config: dict
) -> dict:
    """
    Scores each candidate by:
      score = w1 * expected_delta_pr
            - w2 * cost_estimate
            - w3 * risk_estimate
            + w4 * semantic_confidence
            + w5 * novelty_bonus

    Returns {winner, all_scores, auction_metadata}
    """
    w = auction_config.get("weights", {
        "delta_pr": 1.0,
        "cost": 0.5,
        "risk": 1.0,
        "confidence": 0.3,
        "novelty": 0.1
    })

    scored = []
    for c in candidates:
        score = (
            w["delta_pr"] * c["expected_delta_pr"]
            - w["cost"] * c["cost_estimate"]
            - w["risk"] * c["risk_estimate"]
            + w["confidence"] * c["semantic_confidence"]
            + w["novelty"] * (1.0 if c["source"] == "memory_bank" else 0.0)
        )
        scored.append({**c, "auction_score": score})

    scored.sort(key=lambda x: x["auction_score"], reverse=True)
    winner = scored[0] if scored else None

    return {
        "winner": winner,
        "all_scores": scored,
        "auction_metadata": {
            "n_candidates": len(scored),
            "score_range": (scored[-1]["auction_score"], scored[0]["auction_score"]) if scored else (0, 0),
            "winner_margin": (scored[0]["auction_score"] - scored[1]["auction_score"]) if len(scored) > 1 else 0
        }
    }
```

### Step 8: Spend/Stake Tokens

Commit tokens for the repair. If the repair succeeds, some tokens are returned as a reward. If it fails, tokens are lost.

```python
def spend_tokens(
    token_balance: float,
    winner: dict,
    token_config: dict
) -> dict:
    """
    Deducts repair cost from token balance.
    Returns {new_balance, spent, staked, refund_policy}
    """
    cost = winner["cost_estimate"]
    if token_balance < cost:
        return {
            "status": "insufficient_tokens",
            "new_balance": token_balance,
            "spent": 0,
            "staked": 0
        }

    spent = cost
    stake = cost * token_config.get("stake_fraction", 0.2)
    new_balance = token_balance - spent

    return {
        "status": "committed",
        "new_balance": new_balance,
        "spent": spent,
        "staked": stake,
        "refund_policy": {
            "on_success": f"refund {token_config.get('success_refund', 0.5)} * spent",
            "on_failure": "no refund"
        }
    }
```

### Step 9: Lease Law

Install the repair law in the target mode with a time-limited lease. The law is active for `lease_steps` steps, after which it is evaluated.

```python
def lease_law(
    mode: str,
    winner: dict,
    lease_config: dict
) -> dict:
    """
    Creates a law lease and registers it with the mode.
    Returns {lease_id, law_name, mode, lease_steps, lease_start, lease_end, params}
    """
    lease_id = f"lease_{mode}_{winner['name']}_{int(time.time())}"
    lease_steps = lease_config.get("default_steps", 40)

    lease = {
        "lease_id": lease_id,
        "law_name": winner["name"],
        "mode": mode,
        "policy_fn": winner["policy"],
        "lease_steps": lease_steps,
        "lease_start": current_step(),
        "lease_end": current_step() + lease_steps,
        "params": {
            "source": winner["source"],
            "provenance": winner["provenance"],
            "expected_delta_pr": winner["expected_delta_pr"],
            "semantic_confidence": winner["semantic_confidence"],
            "auction_score": winner["auction_score"]
        },
        "status": "active"
    }

    register_lease(mode, lease)
    return lease
```

### Step 10: Run Validation Window

Execute the target mode for `lease_steps` steps with the leased repair law active. Collect telemetry throughout.

```python
def run_validation_window(
    mode: str,
    lease: dict,
    n_steps: int,
    seed: int = None
) -> dict:
    """
    Runs the mode environment for n_steps with the leased law active.
    Returns {pr_strict_before, pr_strict_after, telemetry_log, events}
    """
    env = create_env(mode, seed=seed)
    baseline_pr = compute_pr_strict(mode, without_law=lease["law_name"])

    telemetry_log = []
    for step in range(n_steps):
        obs = env.get_observation()
        action = lease["policy_fn"](obs)
        next_obs, reward, done, info = env.step(action)
        telemetry_log.append({
            "step": step,
            "observation": obs,
            "action": action,
            "reward": reward,
            "info": info
        })

    post_pr = compute_pr_strict(mode, with_law=lease["law_name"])

    return {
        "pr_strict_before": baseline_pr,
        "pr_strict_after": post_pr,
        "delta_pr": post_pr - baseline_pr,
        "telemetry_log": telemetry_log,
        "events": extract_events(telemetry_log),
        "steps_completed": n_steps
    }
```

### Step 11: Compare Counterfactual

Replay the same seed **without** the repair law to establish causal attribution.

```python
def compare_counterfactual(
    mode: str,
    lease: dict,
    seed: int,
    n_steps: int
) -> dict:
    """
    Runs the mode environment for n_steps WITHOUT the leased law (same seed).
    Returns {pr_strict_counterfactual, pr_strict_with_repair, delta_causal}
    """
    # With repair (already computed)
    with_repair = run_validation_window(mode, lease, n_steps, seed=seed)

    # Without repair (counterfactual)
    counterfactual_env = create_env(mode, seed=seed)
    cf_telemetry = []
    for step in range(n_steps):
        obs = counterfactual_env.get_observation()
        action = counterfactual_env.default_policy(obs)  # no leased law
        next_obs, reward, done, info = counterfactual_env.step(action)
        cf_telemetry.append({"step": step, "reward": reward, "info": info})

    cf_pr = compute_pr_from_telemetry(cf_telemetry)

    delta_causal = with_repair["pr_strict_after"] - cf_pr

    return {
        "pr_strict_counterfactual": cf_pr,
        "pr_strict_with_repair": with_repair["pr_strict_after"],
        "delta_causal": delta_causal,
        "attribution_confidence": (
            "high" if abs(delta_causal) > 0.05
            else "low" if abs(delta_causal) < 0.01
            else "medium"
        )
    }
```

### Step 12: Keep / Quarantine / Mutate

Based on the validation and counterfactual results, decide the fate of the repair law.

```python
def decide_repair_fate(
    validation: dict,
    counterfactual: dict,
    thresholds: dict
) -> str:
    """
    Returns one of: 'keep', 'quarantine', 'mutate', 'discard'
    """
    delta_pr = validation["delta_pr"]
    delta_causal = counterfactual["delta_causal"]

    # Keep: repair clearly improved PR_strict causally
    if delta_pr > thresholds["keep_delta_pr"] and delta_causal > thresholds["keep_causal"]:
        return "keep"

    # Quarantine: repair improved PR_strict but causal attribution is weak
    if delta_pr > thresholds["quarantine_delta_pr"] and delta_causal < thresholds["keep_causal"]:
        return "quarantine"

    # Mutate: repair had partial positive effect but below threshold
    if delta_pr > thresholds["mutate_delta_pr"] and delta_pr <= thresholds["keep_delta_pr"]:
        return "mutate"

    # Discard: repair did not improve or worsened PR_strict
    return "discard"
```

### Step 13: Export Repair Event

Log the entire repair event to the META-K event log for auditing, analysis, and later reference.

```python
def export_repair_event(
    failure: dict,
    candidates: List[dict],
    auction_result: dict,
    token_result: dict,
    lease: dict,
    validation: dict,
    counterfactual: dict,
    fate: str,
    semantic_value: float
) -> dict:
    """
    Creates a complete repair event record.
    """
    return {
        "event_id": f"meta_k_{int(time.time()*1000)}",
        "timestamp": datetime.utcnow().isoformat(),
        "controller_version": "v5.0",
        "failure": failure,
        "n_candidates": len(candidates),
        "auction": {
            "winner": auction_result["winner"]["name"],
            "winner_score": auction_result["winner"]["auction_score"],
            "all_scores": [{c["name"]: c["auction_score"]} for c in auction_result["all_scores"]]
        },
        "tokens": {
            "spent": token_result["spent"],
            "staked": token_result["staked"],
            "refund": token_result["spent"] * 0.5 if fate == "keep" else 0
        },
        "lease": {
            "lease_id": lease["lease_id"],
            "law_name": lease["law_name"],
            "lease_steps": lease["lease_steps"]
        },
        "validation": {
            "pr_before": validation["pr_strict_before"],
            "pr_after": validation["pr_strict_after"],
            "delta_pr": validation["delta_pr"]
        },
        "counterfactual": {
            "pr_without": counterfactual["pr_strict_counterfactual"],
            "pr_with": counterfactual["pr_strict_with_repair"],
            "delta_causal": counterfactual["delta_causal"],
            "attribution": counterfactual["attribution_confidence"]
        },
        "fate": fate,
        "semantic_value": semantic_value,
        "meta_k_energy_after": compute_meta_k_energy()
    }
```

---

## 4. Repair Candidate Example

The following is a complete, realistic repair event as it would appear in the system when META-K handles a colony loop failure:

```json
{
  "event_id": "meta_k_1719384000123",
  "timestamp": "2025-06-26T10:00:00.123Z",
  "controller_version": "v5.0",
  "failure": {
    "mode": "colony",
    "failure": "colony.loop.local_cycle",
    "terminal_state": "looped",
    "subterminal_state": "revisiting_pattern",
    "root_cause": "local_cycle",
    "depth": 1,
    "severity": 0.7,
    "recoverable": true,
    "detected_at_step": 23
  },
  "repair_candidates": [
    {
      "name": "anti_loop_bfs_agent",
      "policy": "bfs_from_current_position_with_unvisited_priority",
      "source": "memory_bank",
      "expected_delta_pr": 0.15,
      "semantic_confidence": 0.88,
      "cost_estimate": 1.2,
      "risk_estimate": 0.08,
      "provenance": "macro_v3"
    },
    {
      "name": "unvisited_neighbor_bias",
      "policy": "prefer_moves_to_unvisited_adjacent_cells",
      "source": "policy_library",
      "expected_delta_pr": 0.08,
      "semantic_confidence": 0.65,
      "cost_estimate": 0.6,
      "risk_estimate": 0.15,
      "provenance": "policy_library_v2"
    },
    {
      "name": "random_escape_mutation",
      "policy": "with_probability_0.3_take_random_action",
      "source": "policy_library",
      "expected_delta_pr": 0.05,
      "semantic_confidence": 0.45,
      "cost_estimate": 0.3,
      "risk_estimate": 0.35,
      "provenance": "policy_library_v1"
    }
  ],
  "chosen": "anti_loop_bfs_agent",
  "lease_steps": 40,
  "expected_delta_pr": 0.12,
  "semantic_confidence": 0.78,
  "lease": {
    "lease_id": "lease_colony_anti_loop_bfs_agent_1719384000",
    "law_name": "anti_loop_bfs_agent",
    "mode": "colony",
    "lease_steps": 40,
    "lease_start": 23,
    "lease_end": 63,
    "status": "active"
  },
  "validation": {
    "pr_strict_before": 0.42,
    "pr_strict_after": 0.58,
    "delta_pr": 0.16
  },
  "counterfactual": {
    "pr_strict_counterfactual": 0.44,
    "pr_strict_with_repair": 0.58,
    "delta_causal": 0.14,
    "attribution": "high"
  },
  "fate": "keep",
  "semantic_value": 0.023,
  "meta_k_energy_after": 85.3
}
```

---

## 5. New Telemetry Columns

The following telemetry columns are added (or extended) for META-K events:

| Column | Type | Description |
|---|---|---|
| `semantic_diagnosis` | `str` | The failure diagnosis produced by META-K. Format: `mode.terminal.subterminal.cause`. |
| `semantic_confidence` | `float` | META-K's confidence in its diagnosis, $\in [0, 1]$. Based on telemetry clarity, grammar match quality, and historical accuracy. |
| `repair_candidate_count` | `int` | Number of repair candidates generated for this failure event. |
| `chosen_repair` | `str` | Name of the repair candidate selected by the auction. |
| `expected_delta_pr` | `float` | Expected improvement in PR_strict from the chosen repair (auction prediction). |
| `actual_delta_pr` | `float` | Measured improvement in PR_strict after the validation window. |
| `counterfactual_delta` | `float` | Causal delta: PR_with_repair - PR_without_repair (same seed). Prevents false attribution. |
| `lease_result` | `str` | Fate of the leased law: `keep`, `quarantine`, `mutate`, or `discard`. |
| `semantic_value` | `float` | $V_{\text{sem}}$ for this repair event. Positive if net helpful, negative if net harmful. |
| `meta_k_energy` | `float` | META-K's remaining energy budget after this repair event. |
| `semantic_version` | `str` | Version identifier of the META-K controller that produced this event (e.g., `v5.0.3`). |
| `repair_provenance_id` | `str` | Unique identifier linking this repair to its source (memory bank entry, policy library entry, or cross-mode port). |

---

## 6. Expected Result

The demo, `demo_05_meta_k_controller.py`, runs the META-K controller across all five modes with injected failures (from Frame 4). The expected outcome:

1. **META-K detects failures** in all five modes using the mode grammars.
2. **META-K generates repair candidates** from memory bank, policy library, dormant revival, and cross-mode porting.
3. **Repair auction selects** the best candidate based on multi-objective scoring.
4. **Tokens are spent** for analysis and repair.
5. **Laws are leased** and validated over the lease window.
6. **Counterfactual replay** confirms causal attribution.
7. **Repairs are kept, quarantined, mutated, or discarded** based on measured impact.
8. **Semantic base PR may remain low** (semantic mode doesn't directly control agents), but **$V_{\text{sem}} > 0$** because it improves other modes' PR_strict.

**Concrete expected numbers:**

| Mode | Failure | Chosen Repair | Expected ΔPR | Actual ΔPR | Counterfactual Δ | Fate | V_sem contribution |
|---|---|---|---|---|---|---|---|
| lander | crash.overspeed | thrust_limit_law | 0.12 | 0.15 | 0.13 | keep | +0.008 |
| pressure | runaway.source_rate | adaptive_valve_law | 0.10 | 0.08 | 0.07 | keep | +0.004 |
| colony | loop.local_cycle | anti_loop_bfs_agent | 0.12 | 0.16 | 0.14 | keep | +0.009 |
| freescape | collision.corner_lock | escape_corner_agent | 0.08 | 0.06 | 0.05 | quarantine | +0.002 |
| semantic | repair_failure.noise_attribution | clean_diagnosis_protocol | 0.05 | 0.03 | 0.02 | mutate | +0.001 |

**Aggregate:** $V_{\text{sem}}^{(5)} = 0.024 > 0$. META-K is net helpful despite spending tokens on some partially effective repairs.

---

## 7. Build Files

```
examples/core_tier/v5_demo_05/
├── demo_05_meta_k_controller.py       # Main demo: orchestrates META-K loop across all modes
├── semantic_controller.py              # META-K controller implementation (13-step loop)
├── repair_planner.py                   # Generates repair candidates from multiple sources
├── repair_auction.py                   # Multi-objective repair scoring and selection
├── causal_inference.py                 # Counterfactual replay and causal attribution
├── meta_k_events.jsonl                 # JSONL log: one complete repair event per intervention
├── semantic_value.csv                  # CSV: V_sem over time, per mode, per repair type
└── report_meta_k_controller.md         # Auto-generated report: controller performance analysis
```

**File descriptions:**

| File | Purpose |
|---|---|
| `demo_05_meta_k_controller.py` | Entry point. Initializes all modes, runs failure injection (reusing Frame 4's injector), activates META-K on each failure, collects telemetry, writes outputs. |
| `semantic_controller.py` | Implements the `MetaKController` class with the 13-step loop. Manages energy budget, law leases, and rolling V_sem computation. |
| `repair_planner.py` | `RepairPlanner` class that generates candidates from memory bank, policy library, dormant revival, and cross-mode porting. Also handles mutation of partially-successful repairs. |
| `repair_auction.py` | `RepairAuction` class that scores candidates using configurable multi-objective weights. Outputs winner and full ranking. |
| `causal_inference.py` | `CausalInference` class that runs counterfactual replays (same seed, without repair). Computes $\Delta PR_{\text{causal}}$ and attribution confidence. |
| `meta_k_events.jsonl` | One JSON object per META-K intervention. Contains all 13 steps' outputs: failure detection, candidates, auction, tokens, lease, validation, counterfactual, fate, semantic value. |
| `semantic_value.csv` | Time series of $V_{\text{sem}}$ with columns: `timestamp`, `repair_number`, `V_sem`, `V_sem_rolling_10`, `delta_pr_cross`, `analysis_cost`, `tokens_wasted`, `meta_k_energy`, `controller_version`. |
| `report_meta_k_controller.md` | Generated report with: V_sem trend plot, per-mode contribution breakdown, repair success rate, false attribution rate, energy utilization, top repairs by semantic value. |

---

## 8. Integrated Enhancements 33–40

### Enhancement 33: META-K Policy Library

**Description:** A comprehensive library of repair policies that META-K can draw from. Each policy is tagged with the failure classes it addresses, its expected performance, and its cost. The library supports the following policy types:

| Policy Type | Description | Example |
|---|---|---|
| `prune` | Remove a law that is causing harm. | Remove `aggressive_descent_law` from lander after crash. |
| `mutate` | Modify parameters of an existing law. | Reduce `pressure_valve_gain` from 2.0 to 0.8 after runaway. |
| `lease` | Temporarily install a new repair law. | Lease `anti_loop_bfs_agent` for 40 steps in colony. |
| `swap` | Replace one law with another. | Swap `greedy_explorer` with `bfs_explorer` in colony. |
| `inject_noise` | Add stochastic perturbation to break deterministic loops. | Add $\mathcal{N}(0, \sigma)$ noise to colony movement policy. |
| `extend_budget` | Increase resource allocation to a failing mode. | Give colony mode 20% more energy tokens. |
| `quarantine` | Isolate a law without removing it (for later analysis). | Quarantine `phase_shift_collision` law pending investigation. |
| `revive_dormant` | Re-activate a previously dormant law. | Revive `conservative_throttle` after new failure pattern detected. |
| `port_cross_mode_law` | Transfer a repair law from one mode to another. | Port lander's `velocity_smoother` to freescape as `height_smoother`. |

**Library structure:**

```python
POLICY_LIBRARY = {
    "lander.crash": [
        {
            "name": "thrust_limit_law",
            "type": "lease",
            "policy_fn": "cap_thrust_to_safe_maximum",
            "expected_delta_pr": 0.12,
            "confidence": 0.85,
            "cost": 1.0,
            "risk": 0.10,
            "version": 3
        },
        {
            "name": "prune_aggressive_descent",
            "type": "prune",
            "policy_fn": "remove_law('aggressive_descent_law')",
            "expected_delta_pr": 0.08,
            "confidence": 0.70,
            "cost": 0.3,
            "risk": 0.05,
            "version": 1
        }
    ],
    "colony.loop": [
        {
            "name": "anti_loop_bfs_agent",
            "type": "lease",
            "policy_fn": "bfs_from_current_position_with_unvisited_priority",
            "expected_delta_pr": 0.15,
            "confidence": 0.88,
            "cost": 1.2,
            "risk": 0.08,
            "version": 3
        },
        {
            "name": "inject_exploration_noise",
            "type": "inject_noise",
            "policy_fn": "add_noise(sigma=0.3)",
            "expected_delta_pr": 0.05,
            "confidence": 0.50,
            "cost": 0.2,
            "risk": 0.35,
            "version": 1
        }
    ],
    # ... entries for all failure classes across all modes
}
```

---

### Enhancement 34: Repair Impact Prediction

**Description:** Train a small regression model that predicts the expected $\Delta PR_{\text{strict}}$ for a repair candidate before it is deployed. This model takes features from the current law state, failure features, and mode features, and outputs a predicted impact score. This improves auction bid accuracy and reduces wasted tokens on unlikely-to-succeed repairs.

**Model architecture:**

```
Input features:
  - Law features: n_active_laws, n_leased_laws, law_complexity_mean, law_age_mean,
    dependency_density, conflict_count
  - Failure features: failure_severity, failure_depth, time_since_failure,
    same_failure_count (how often this exact failure has occurred), recovery_attempts
  - Mode features: mode_pr_strict, mode_pr_strict_trend (slope over last 100 steps),
    mode_r_recover, mode_e_recover, mode_token_balance
  - Candidate features: candidate_type (one-hot), candidate_cost, candidate_risk,
    candidate_source (memory_bank/policy_library/dormant/cross_mode)

Output:
  - expected_delta_pr (scalar, ∈ [-1, 1])

Architecture: 3-layer MLP, 64-32-16 hidden units, ReLU, output linear
Training: MSE loss on historical repair events
Regularization: L2 (λ=0.01), dropout (p=0.1)
```

**Usage in auction:**

```python
def predict_repair_impact(
    candidate: dict,
    law_features: np.ndarray,
    failure_features: np.ndarray,
    mode_features: np.ndarray,
    model: RepairImpactModel
) -> float:
    """
    Predicts expected delta PR for a repair candidate.
    Combines model prediction with candidate's self-reported expected_delta_pr.
    """
    candidate_features = encode_candidate_features(candidate)
    all_features = np.concatenate([law_features, failure_features, mode_features, candidate_features])

    model_prediction = model.predict(all_features)
    self_reported = candidate["expected_delta_pr"]

    # Weighted blend: trust model more as it accumulates training data
    model_weight = min(0.8, model.n_training_samples / 500)
    blended = model_weight * model_prediction + (1 - model_weight) * self_reported

    return blended
```

---

### Enhancement 35: Counterfactual Replay

**Description:** After a repair is validated, replay the exact same episode seed **without** the repair to establish causal attribution. The difference between PR_strict with repair and PR_strict without repair is the causal delta:

$$\Delta PR_{\text{causal}} = PR_{\text{strict}}^{\text{with repair}} - PR_{\text{strict}}^{\text{without repair}}$$

This prevents false attribution where PR_strict improves due to random seed variation, external mode interactions, or temporal trends rather than the repair itself.

**Implementation details:**

- Both the repair run and the counterfactual run use the **same random seed**.
- The counterfactual run uses the **default policy** (no leased law).
- The counterfactual run starts from the **same state** as the repair run (the failure state).
- Attribution confidence is assigned:
  - **High:** $|\Delta PR_{\text{causal}}| > 0.05$ and consistent across 3+ counterfactual runs with different seeds.
  - **Medium:** $0.01 < |\Delta PR_{\text{causal}}| \leq 0.05$.
  - **Low:** $|\Delta PR_{\text{causal}}| \leq 0.01$ or inconsistent across seeds.

**Multi-seed validation:**

```python
def multi_seed_counterfactual(
    mode: str,
    lease: dict,
    base_seed: int,
    n_seeds: int = 5,
    n_steps: int = 40
) -> dict:
    """
    Run counterfactual with multiple seeds to assess robustness of causal attribution.
    """
    results = []
    for i in range(n_seeds):
        seed = base_seed + i
        cf = compare_counterfactual(mode, lease, seed, n_steps)
        results.append(cf["delta_causal"])

    mean_delta = np.mean(results)
    std_delta = np.std(results)
    consistency = 1.0 - min(1.0, std_delta / max(abs(mean_delta), 0.01))

    return {
        "deltas": results,
        "mean_delta": mean_delta,
        "std_delta": std_delta,
        "consistency": consistency,
        "attribution_confidence": (
            "high" if mean_delta > 0.05 and consistency > 0.7
            else "medium" if mean_delta > 0.01
            else "low"
        )
    }
```

---

### Enhancement 36: Semantic Cross-Mode Attention

**Description:** Maintain an attention matrix that captures the relevance of failures and repairs across modes. This enables META-K to discover that, for example, colony loop fixes may inform freescape collision locks (both involve getting stuck in bounded spaces), or that pressure runaway diagnostics may help lander approach-to-fast detection (both involve rate-based failures).

**Attention matrix:**

$$A_{ij} = \frac{\text{sim}(\text{failure}_i, \text{failure}_j) \cdot \text{sim}(\text{repair}_i, \text{repair}_j)}{1 + d_{\text{mode}}(i, j)}$$

Where:
- $\text{sim}(\cdot, \cdot)$ is a cosine similarity in failure/repair feature space.
- $d_{\text{mode}}(i, j)$ is the mode distance (0 if same mode, 1 if different mode, 2 if very different mode).
- $A_{ij} \in [0, 1]$; higher values mean mode $i$'s failures/repairs are more relevant to mode $j$.

**Example attention matrix (simplified):**

| | Lander | Pressure | Colony | Freescape | Semantic |
|---|---|---|---|---|---|
| **Lander** | 1.00 | 0.15 | 0.08 | 0.22 | 0.05 |
| **Pressure** | 0.15 | 1.00 | 0.12 | 0.18 | 0.05 |
| **Colony** | 0.08 | 0.12 | 1.00 | 0.45 | 0.05 |
| **Freescape** | 0.22 | 0.18 | 0.45 | 1.00 | 0.05 |
| **Semantic** | 0.05 | 0.05 | 0.05 | 0.05 | 1.00 |

**Interpretation:** Colony and Freescape have high cross-mode relevance (0.45) because both involve spatial navigation and getting stuck. Lander and Freescape have moderate relevance (0.22) because both involve velocity and collision management.

**Usage:**

When META-K encounters a failure in Colony that it has not seen before, it checks the attention matrix to find the most relevant other mode (Freescape, 0.45) and imports repair candidates from that mode's successful repairs, adapted as needed.

```python
def find_cross_mode_repairs(
    failure: dict,
    policy_library: dict,
    attention_matrix: np.ndarray,
    mode_index: dict
) -> List[dict]:
    """
    Finds repair candidates from other modes based on cross-mode attention.
    """
    source_mode = failure["mode"]
    source_idx = mode_index[source_mode]

    # Find modes most relevant to source_mode
    attentions = attention_matrix[source_idx]
    sorted_modes = np.argsort(-attentions)

    cross_candidates = []
    for target_idx in sorted_modes:
        target_mode = mode_index[target_idx]
        if target_mode == source_mode:
            continue
        if attentions[target_idx] < 0.2:  # attention threshold
            break

        failure_class = f"{target_mode}.{failure['terminal']}"
        for policy in policy_library.get(failure_class, []):
            cross_candidates.append({
                "name": f"port_{policy['name']}_from_{target_mode}",
                "policy": policy["policy_fn"],
                "source": "cross_mode_port",
                "source_mode": target_mode,
                "attention_score": attentions[target_idx],
                "expected_delta_pr": policy["expected_delta_pr"] * attentions[target_idx],
                "semantic_confidence": policy["confidence"] * attentions[target_idx] * 0.5,
                "cost_estimate": policy["cost"] * 1.2,  # 20% surcharge for cross-mode adaptation
                "risk_estimate": policy["risk"] * 1.5,  # higher risk for cross-mode
                "provenance": f"port_{target_mode}_v{policy.get('version', 1)}"
            })

    return cross_candidates
```

---

### Enhancement 37: Multi-Objective Repair Ranking

**Description:** Rank repair candidates using Pareto-optimal front over multiple objectives, not a single score. This avoids single-metric myopia where a repair with high expected ΔPR but extreme risk or cost would be selected.

**Objectives:**

1. $\Delta PR_{\text{strict}}$ — higher is better.
2. Token cost — lower is better.
3. Risk delta ($\Delta R_{\text{risk}}$) — lower is better (repair should not increase risk).
4. Novelty delta — higher is better (prefer novel repairs over well-trodden ones).
5. Runtime cost — lower is better (repair should not slow the system significantly).

**Pareto front computation:**

```python
def pareto_rank_repairs(
    candidates: List[dict],
    objectives: List[str] = [
        "expected_delta_pr",      # maximize
        "cost_estimate",           # minimize
        "risk_estimate",           # minimize
        "novelty_score",           # maximize
        "runtime_estimate"         # minimize
    ]
) -> List[dict]:
    """
    Computes Pareto front of repair candidates.
    Returns candidates sorted by dominance rank.
    """
    # Build objective matrix: shape (n_candidates, n_objectives)
    # Normalize so all objectives are "maximize" (negate minimization objectives)
    matrix = np.array([
        [
            c["expected_delta_pr"],
            -c["cost_estimate"],
            -c["risk_estimate"],
            c.get("novelty_score", 0.0),
            -c.get("runtime_estimate", 0.0)
        ]
        for c in candidates
    ])

    # Compute Pareto ranks using non-dominated sorting
    ranks = np.zeros(len(candidates), dtype=int)
    dominated_by = [set() for _ in candidates]
    dominates = [set() for _ in candidates]

    for i in range(len(candidates)):
        for j in range(len(candidates)):
            if i == j:
                continue
            if np.all(matrix[i] >= matrix[j]) and np.any(matrix[i] > matrix[j]):
                dominates[i].add(j)
                dominated_by[j].add(i)

    # Assign ranks
    current_front = [i for i in range(len(candidates)) if not dominated_by[i]]
    rank = 1
    while current_front:
        for i in current_front:
            ranks[i] = rank
        next_front = set()
        for i in current_front:
            for j in dominates[i]:
                dominated_by[j].discard(i)
                if not dominated_by[j]:
                    next_front.add(j)
        current_front = list(next_front)
        rank += 1

    # Sort by Pareto rank, then by auction score within same rank
    ranked_candidates = sorted(
        zip(candidates, ranks),
        key=lambda x: (x[1], -x[0].get("auction_score", 0))
    )

    return [c for c, r in ranked_candidates]
```

---

### Enhancement 38: Repair Sandbox

**Description:** Before committing a repair to the live system, simulate a short future horizon in a low-cost sandbox environment. The sandbox runs the mode with the proposed repair for a small number of steps and checks for red flags.

**Rejection criteria (any one causes rejection):**

1. **Risk rises:** $R_{\text{risk}}^{\text{sandbox}} > R_{\text{risk}}^{\text{current}} + \epsilon_{\text{risk}}$.
2. **PR_strict drops:** $PR_{\text{strict}}^{\text{sandbox}} < PR_{\text{strict}}^{\text{current}} - \epsilon_{\text{pr}}$.
3. **Token cost too high:** $C_{\text{sandbox}} > C_{\text{budget}} \cdot \theta_{\text{cost}}$.
4. **Stagnation increases:** Agent's state diversity (entropy of visited states) decreases.
5. **Catastrophic failure in sandbox:** Any terminal state with severity > 0.8 during the sandbox run.

**Implementation:**

```python
def sandbox_validate(
    mode: str,
    candidate: dict,
    current_state: dict,
    sandbox_steps: int = 30,
    thresholds: dict = None
) -> dict:
    """
    Runs a short sandbox simulation with the proposed repair.
    Returns {accepted, reasons, sandbox_metrics}
    """
    if thresholds is None:
        thresholds = {
            "max_risk_increase": 0.1,
            "max_pr_drop": 0.05,
            "max_cost_ratio": 0.3,
            "min_entropy_delta": -0.1,
            "max_catastrophic_severity": 0.8
        }

    env = create_env(mode)
    env.set_state(current_state)

    sandbox_telemetry = []
    catastrophic = False

    for step in range(sandbox_steps):
        obs = env.get_observation()
        action = candidate["policy_fn"](obs)
        next_obs, reward, done, info = env.step(action)
        sandbox_telemetry.append(info)

        if info.get("severity", 0) > thresholds["max_catastrophic_severity"]:
            catastrophic = True
            break

    metrics = compute_sandbox_metrics(sandbox_telemetry, current_state)

    rejection_reasons = []
    if metrics["risk_delta"] > thresholds["max_risk_increase"]:
        rejection_reasons.append("risk_rise")
    if metrics["pr_delta"] < -thresholds["max_pr_drop"]:
        rejection_reasons.append("pr_drop")
    if metrics["cost_ratio"] > thresholds["max_cost_ratio"]:
        rejection_reasons.append("cost_too_high")
    if metrics["entropy_delta"] < thresholds["min_entropy_delta"]:
        rejection_reasons.append("stagnation")
    if catastrophic:
        rejection_reasons.append("catastrophic_failure")

    return {
        "accepted": len(rejection_reasons) == 0,
        "rejection_reasons": rejection_reasons,
        "sandbox_metrics": metrics,
        "catastrophic": catastrophic
    }
```

---

### Enhancement 39: Semantic Value Ledger

**Description:** Track rolling semantic ROI to prevent one early lucky repair from inflating the controller's score. The ledger maintains multiple granularities of V_sem:

| Granularity | Description | Update Frequency |
|---|---|---|
| `V_sem_last_10` | Mean V_sem over the last 10 repairs | After each repair |
| `V_sem_last_50` | Mean V_sem over the last 50 repairs | After each repair |
| `V_sem_by_mode[m]` | Mean V_sem for repairs targeting mode m | After each repair targeting m |
| `V_sem_by_type[t]` | Mean V_sem for repairs of type t (lease/prune/mutate/etc.) | After each repair of type t |
| `V_sem_by_version[v]` | Mean V_sem for controller version v | After each repair by version v |
| `V_sem_cumulative` | Total cumulative V_sem since controller initialization | After each repair |

**Ledger structure:**

```python
@dataclass
class SemanticValueLedger:
    history: List[float] = field(default_factory=list)  # V_sem per repair
    by_mode: Dict[str, List[float]] = field(default_factory=dict)
    by_type: Dict[str, List[float]] = field(default_factory=dict)
    by_version: Dict[str, List[float]] = field(default_factory=dict)

    def record(self, v_sem: float, mode: str, repair_type: str, version: str):
        self.history.append(v_sem)
        self.by_mode.setdefault(mode, []).append(v_sem)
        self.by_type.setdefault(repair_type, []).append(v_sem)
        self.by_version.setdefault(version, []).append(v_sem)

    def rolling(self, n: int) -> float:
        if not self.history:
            return 0.0
        return np.mean(self.history[-n:])

    def cumulative(self) -> float:
        return sum(self.history)

    def by_mode_rolling(self, mode: str, n: int) -> float:
        hist = self.by_mode.get(mode, [])
        if not hist:
            return 0.0
        return np.mean(hist[-n:])

    def summary(self) -> dict:
        return {
            "v_sem_last_10": self.rolling(10),
            "v_sem_last_50": self.rolling(50),
            "v_sem_cumulative": self.cumulative(),
            "total_repairs": len(self.history),
            "positive_repairs": sum(1 for v in self.history if v > 0),
            "negative_repairs": sum(1 for v in self.history if v < 0),
            "by_mode": {m: self.rolling(10) for m in self.by_mode},
            "by_type": {t: self.rolling(10) for t in self.by_type},
            "by_version": {v: self.rolling(10) for v in self.by_version}
        }
```

---

### Enhancement 40: Self-Awareness Dashboard

**Description:** A live dashboard that makes META-K's internal state legible to human operators and to META-K itself (enabling self-reflection). The dashboard displays:

**Panel 1: Current Diagnosis**

| Field | Value |
|---|---|
| Active failures | `colony.loop.local_cycle`, `lander.crash.overspeed` |
| Highest severity | `lander.crash.overspeed` (severity: 0.9) |
| Cascade probability | $P_{\text{cascade}} = 0.35$ |
| Emergency mode | OFF |

**Panel 2: Repair Queue**

| Priority | Mode | Failure | Candidate | Status | Expected ΔPR |
|---|---|---|---|---|---|
| 1 | lander | crash.overspeed | thrust_limit_law | validating | 0.12 |
| 2 | colony | loop.local_cycle | anti_loop_bfs_agent | queued | 0.15 |
| 3 | pressure | runaway.source_rate | adaptive_valve_law | queued | 0.10 |

**Panel 3: Token Balances**

| Mode | Balance | Budget | Utilization |
|---|---|---|---|
| META-K | 85.3 | 100.0 | 14.7% spent |
| Lander | 22.1 | 30.0 | 26.3% spent |
| Colony | 18.5 | 25.0 | 26.0% spent |
| Pressure | 15.0 | 20.0 | 25.0% spent |
| Freescape | 12.0 | 20.0 | 40.0% spent |
| Semantic | 8.2 | 10.0 | 18.0% spent |

**Panel 4: Expected vs Actual ΔPR**

```
Repair  | Expected | Actual | Counterfactual | Attribution
--------|----------|--------|----------------|------------
RL_001  | 0.12     | 0.15   | 0.13           | high
RL_002  | 0.10     | 0.08   | 0.07           | medium
RL_003  | 0.15     | 0.16   | 0.14           | high
RL_004  | 0.08     | 0.06   | 0.05           | medium
RL_005  | 0.05     | 0.03   | 0.02           | low
```

**Panel 5: Active Law Leases**

| Lease ID | Law | Mode | Steps Remaining | Status |
|---|---|---|---|---|
| LL_001 | thrust_limit_law | lander | 12 | active |
| LL_002 | anti_loop_bfs_agent | colony | 28 | active |
| LL_003 | adaptive_valve_law | pressure | 0 | expired |

**Panel 6: Semantic Confidence & Value**

```
V_sem (last 10):     +0.024
V_sem (last 50):     +0.018
V_sem (cumulative):  +1.247
Controller version:  v5.0.3
Positive repairs:    42 / 50 (84%)
Negative repairs:    8 / 50 (16%)
```

**Implementation:**

The dashboard is generated as structured data (JSON) that can be rendered as:
- A terminal-based text dashboard (for headless environments).
- An HTML page (for browser viewing).
- A structured log entry (for programmatic consumption).

```python
def generate_dashboard(
    global_view: dict,
    repair_queue: List[dict],
    lease_registry: List[dict],
    semantic_ledger: SemanticValueLedger,
    controller_version: str
) -> dict:
    """
    Generates the full self-awareness dashboard as structured data.
    """
    return {
        "current_diagnosis": {
            "active_failures": [
                {
                    "mode": f["mode"],
                    "failure": f"{f['mode']}.{f['terminal']}.{f['subterminal']}.{f['cause']}",
                    "severity": f["severity"]
                }
                for f in detect_failure_class(global_view, ALL_GRAMMARS)
            ],
            "cascade_probability": global_view["global"]["cascade_probability"],
            "emergency_mode": global_view["global"]["cascade_probability"] > 0.7
        },
        "repair_queue": [
            {
                "priority": i + 1,
                "mode": r["mode"],
                "failure": r["failure_class"],
                "candidate": r["chosen_repair"],
                "status": r["status"],
                "expected_delta_pr": r["expected_delta_pr"]
            }
            for i, r in enumerate(repair_queue)
        ],
        "token_balances": {
            mode: {
                "balance": data["token_balance"],
                "budget": data.get("token_budget", 0),
                "utilization": 1.0 - data["token_balance"] / max(data.get("token_budget", 1), 1)
            }
            for mode, data in global_view["modes"].items()
        },
        "active_leases": [
            {
                "lease_id": l["lease_id"],
                "law": l["law_name"],
                "mode": l["mode"],
                "steps_remaining": max(0, l["lease_end"] - current_step()),
                "status": l["status"]
            }
            for l in lease_registry if l["status"] == "active"
        ],
        "semantic_confidence_and_value": semantic_ledger.summary(),
        "controller_version": controller_version,
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

## 9. Complete Demo Script Outline

```python
#!/usr/bin/env python3
"""
demo_05_meta_k_controller.py — Frame 5: Semantic META-K Controller Demo

This demo validates:
1. META-K detects failures across all modes using mode grammars.
2. META-K generates repair candidates from multiple sources.
3. Repair auction selects the best candidate using multi-objective ranking.
4. Tokens are spent, laws are leased, and validation windows are run.
5. Counterfactual replay establishes causal attribution.
6. Repairs are kept, quarantined, mutated, or discarded.
7. V_sem > 0, proving META-K is net helpful despite its own low PR_strict.

Usage:
    python demo_05_meta_k_controller.py --episodes 100 --controller-version v5.0
    python demo_05_meta_k_controller.py --episodes 50 --inject-all-modes
"""

import argparse
import json
import csv
import numpy as np
from pathlib import Path
from datetime import datetime

from semantic_controller import MetaKController
from repair_planner import RepairPlanner
from repair_auction import RepairAuction
from causal_inference import CausalInference
from mode_grammars import load_grammars

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--controller-version", default="v5.0")
    parser.add_argument("--output-dir", default=".")
    args = parser.parse_args()

    grammars = load_grammars("mode_grammars.yaml")

    # Initialize META-K controller
    controller = MetaKController(
        version=args.controller_version,
        grammars=grammars,
        energy_budget=100.0,
        policy_library_path="policy_library.json",
        memory_bank_path="failure_memory_bank.json"
    )

    # Run episodes
    meta_k_events = []
    semantic_values = []

    for ep in range(args.episodes):
        # Run all modes (with failure injection from Frame 4)
        mode_telemetry = run_all_modes(ep)

        # Activate META-K
        event = controller.step(mode_telemetry)
        if event is not None:
            meta_k_events.append(event)
            semantic_values.append(event["semantic_value"])

    # Write outputs
    write_meta_k_events(meta_k_events, Path(args.output_dir) / "meta_k_events.jsonl")
    write_semantic_value_csv(semantic_values, Path(args.output_dir) / "semantic_value.csv")
    generate_report(meta_k_events, semantic_values, Path(args.output_dir) / "report_meta_k_controller.md")

    # Print summary
    ledger = controller.get_ledger_summary()
    print(f"V_sem (last 10): {ledger['v_sem_last_10']:.4f}")
    print(f"V_sem (last 50): {ledger['v_sem_last_50']:.4f}")
    print(f"Total repairs: {ledger['total_repairs']}")
    print(f"Positive repairs: {ledger['positive_repairs']}")
    print(f"Controller is net helpful: {ledger['v_sem_last_10'] > 0}")

if __name__ == "__main__":
    main()
```

---

## 10. Summary

Frame 5 elevates semantic mode from passive observer to active causal director. The META-K controller:

- **Observes** all modes through a unified telemetry interface.
- **Diagnoses** failures using rich mode grammars (from Frame 4).
- **Proposes** repairs from a diverse policy library, failure memory bank, dormant law revival, and cross-mode porting.
- **Selects** repairs through multi-objective Pareto ranking and repair impact prediction.
- **Validates** repairs in sandboxes and through counterfactual replay.
- **Tracks** its own value through a semantic value ledger with multiple granularities.
- **Makes itself legible** through a self-awareness dashboard.

The key insight: META-K's own PR_strict may remain low (it doesn't control physical agents), but $V_{\text{sem}} > 0$ proves it is causally beneficial. This is the first demonstration of **semantic utility** in the RGPUF system.
