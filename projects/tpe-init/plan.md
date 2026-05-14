# TPE-Init: Bayesian Optimization over Initialization Space with Trajectory Pruning

## Novelty Assessment

### Idea 1 — TPE over initializations + successive halving of trajectories

**Is this trivial?** No, but there is a very close prior: **BOHB** (Bayesian Optimization and
Hyperband, Falkner et al. 2018) already combines TPE with Hyperband-style successive halving.
The standard framing is over *hyperparameter* configurations (lr, wd, architecture choices).

What makes the framing here distinct — and potentially publishable:

1. **The search space is the initialization manifold, not the hyperparameter space.**  
   TPE proposes weight initializations (seed, init scheme params, scale) rather than
   learning rate / architecture flags. The loss trajectory then reflects the geometry of the
   loss landscape from that starting point. This is closer to basin-of-attraction analysis
   than standard HPO.

2. **Pruning uses trajectory shape, not just loss value.**  
   A training run from a bad initialization shows distinct curvature / gradient norm signatures
   early on (large oscillations, slow descent, high gradient variance). Incorporating these
   as features for pruning — not just raw loss — is richer than what ASHA/Hyperband do.

3. **TPE learns a model of "good starting regions" from observed trajectories.**  
   Standard BOHB treats final val loss as the signal. Here the signal could be:
   - Final loss at pruning checkpoint
   - Area under the loss curve (converging fast is worth more than converging slow)
   - Gradient-to-weight ratio at checkpoints (stability signal from Tutorial 4-style monitoring)

**Related work to distinguish from:**
- BOHB (Falkner et al., 2018) — closest; uses TPE + Hyperband over hyperparams
- Population-Based Training (Jaderberg et al., 2017) — online adaptation, no Bayesian model
- Loss of Plasticity / Sharpness-Aware Minimization — different angle on initialization geometry
- Neural Tangent Kernel warm-start — theoretical angle on initialization importance

**The gap:** No existing work uses TPE to explicitly search the *initialization distribution*
and prunes based on *trajectory features* (not just terminal performance).

---

### Idea 2 — AutoResearch → Optuna pipeline

**Is this trivial?** Moderately novel as a *pipeline*, less so as individual components.

The key insight: use an LLM to identify *which hyperparameters matter* (sensitivity analysis
via natural language reasoning over training logs / loss curves), then run Optuna only on
those. This reduces search dimensionality by structured reasoning rather than ablation.

Prior work: AutoML-GPT, FunSearch, LLM-as-optimizer. The gap is the *two-stage* nature:
LLM for sensitivity identification → Bayesian HPO on the reduced space.

This pairs naturally with Idea 1: AutoResearch identifies important initialization hyperparams,
TPE-Init searches them efficiently.

---

## System Design

### Idea 1: TPE-Init Algorithm

```
Input: model_factory(), train_loader, val_loader, budget B, rounds R
       init_search_space (seed range, init_scale range, init_scheme ∈ {kaiming, xavier, ...})

Phase 1 — Initial population (round 0):
  1. Sample n_init configurations from init_search_space (Sobol sequence or random)
  2. Train each for B_0 steps (small initial budget)
  3. Record trajectory features: (loss curve, grad_norm curve, grad/weight ratio curve)
  4. Score each: score = f(val_loss, convergence_speed, trajectory_stability)

Phase 2 — Successive rounds:
  for r in 1..R:
    1. Fit TPE model on (init_configs, scores) from all previous rounds
    2. Use TPE to propose n_r new configurations (exploitation + exploration)
    3. Train new configs for B_r = B_0 * eta^r steps (increasing budget)
    4. Prune: keep top-k% by score from this round + all survivors from previous rounds
    5. Update TPE model with new observations

Output: best initialization config + trained model
```

**Key design choices:**
- `eta = 3` (Hyperband default), `n_init = 9`, `B_0 = 100 steps`
- Trajectory feature vector: `[loss@25%, loss@50%, loss@75%, mean_grad_ratio, std_loss_curve]`
- Score function: `score = -val_loss * (1 + penalty * std_loss_curve)` (penalize instability)
- TPE operates on the **feature space** of trajectories, not just terminal loss

### Idea 2: AutoResearch + Optuna pipeline

```
Phase 1 — AutoResearch (LLM-guided sensitivity identification):
  1. Run k short training runs with varied configs (random search, low budget)
  2. Log: loss curves, gradient stats, hyperparameter values
  3. Prompt LLM with structured summary of runs:
     "Given these training logs, which hyperparameters show the highest
      sensitivity (small change → large loss difference)? Rank them."
  4. Extract top-m hyperparameters from LLM response
  5. Optionally: LLM proposes new architecture variants to try

Phase 2 — Optuna TPE on reduced space:
  1. Define search space over only the top-m identified hyperparameters
  2. Run standard Optuna TPE study with full budget
  3. Use ASHA pruner for early stopping within trials

Integration with Idea 1:
  - AutoResearch identifies important init hyperparameters
  - TPE-Init searches them with trajectory-aware pruning
```

---

## Experiments

### Experiment 1: Validate initialization sensitivity justification
- Train NanoGPT (Tutorial 2 architecture) from 100 different random seeds
- Measure: correlation between init seed and final val loss at 5000 steps
- Expected result: non-trivial variance — confirms the search space is meaningful

### Experiment 2: TPE-Init vs baselines
- **Baselines:** random search + Hyperband (ASHA), BOHB over hyperparams
- **Metric:** val loss at equal total compute (tokens processed, not wall time)
- **Dataset:** TinyShakespeare (fast iteration) → FineWeb-Edu subset
- **Models:** NanoGPT 10M, and one larger (125M if feasible)

### Experiment 3: Trajectory features vs terminal loss for pruning
- Compare pruning strategies:
  - ASHA (prune by val loss at checkpoint)
  - Trajectory-feature pruning (prune by score = f(loss curve, grad stats))
- Does richer trajectory information improve final outcome at equal budget?

### Experiment 4: AutoResearch sensitivity identification accuracy
- Ground truth: full ablation over each hyperparameter independently
- LLM prediction: rank hyperparameters from training logs
- Metric: rank correlation (Spearman's ρ) between LLM ranking and ablation ranking

### Experiment 5: Combined pipeline
- AutoResearch → TPE-Init on the identified important init params
- Compare to: standard BOHB over all hyperparameters
- Metric: final val loss at equal total compute

---

## Implementation Plan

### Phase 1 — Infrastructure (Week 1)
- [ ] `tpe_init/trajectory.py` — trajectory recording and feature extraction
  - Hook into training loop (Tutorial 5 logger style)
  - Feature: `TrajectoryFeatures(loss_curve, grad_ratio_curve, val_checkpoints)`
- [ ] `tpe_init/scorer.py` — configurable score function
- [ ] `tpe_init/pruner.py` — trajectory-aware pruner (implements Optuna `BasePruner`)

### Phase 2 — TPE-Init Core (Week 2)
- [ ] `tpe_init/sampler.py` — wrap Optuna TPESampler with init_search_space
- [ ] `tpe_init/runner.py` — orchestrates rounds: sample → train → score → update
- [ ] Integration with NanoGPT training loop from Tutorial 9

### Phase 3 — AutoResearch (Week 3)
- [ ] `autoresearch/logger.py` — structured training summary for LLM prompting
- [ ] `autoresearch/prompt.py` — prompt templates for sensitivity analysis
- [ ] `autoresearch/pipeline.py` — full AutoResearch → Optuna pipeline

### Phase 4 — Experiments (Week 4-5)
- [ ] Experiments 1-3 (core validation)
- [ ] Experiments 4-5 (combined pipeline)
- [ ] Plots: loss-vs-compute curves, pruning survival diagrams, sensitivity rankings

---

## Open Questions

1. **What is the right trajectory feature?** Gradient-to-weight ratio from Tutorial 4 is a
   natural candidate (captures init quality directly). But it requires hooks — adds overhead.

2. **Does TPE over initialization matter more for some architectures?**  
   Transformers with residual connections are less sensitive to init than deep CNNs.
   May need to verify the effect size justifies the search overhead.

3. **How does the LLM sensitivity analysis perform on architecture choices vs scalar params?**  
   Architecture choices (depth, width, attention heads) are categorical — TPE handles these
   differently. The LLM may be better at ranking continuous params.

4. **Budget accounting.** Does the compute overhead of TPE oracle calls matter at the scale
   of 10M-parameter training? Probably not, but worth profiling.

---

## References

- Falkner, Klein, Hutter (2018). *BOHB: Robust and Efficient Hyperparameter Optimization at Scale.*
- Li, Jamieson, et al. (2018). *Hyperband: A Novel Bandit-Based Approach to Hyperparameter Optimization.*
- Jaderberg, Dalibard, et al. (2017). *Population Based Training of Neural Networks.*
- Akiba, Sano, et al. (2019). *Optuna: A Next-generation Hyperparameter Optimization Framework.*
