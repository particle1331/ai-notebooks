import numpy as np


# ── Helpers ────────────────────────────────────────────────────────────────────

def allclose(a, b, atol=1e-9, label=""):
    ok = np.allclose(a, b, atol=atol)
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {label}  (max_err={np.max(np.abs(a - b)):.2e})")
    return ok


# ── Manual SVD walkthrough ─────────────────────────────────────────────────────
#
# For A (m×n), SVD gives A = U Σ Vᵀ where:
#   U  : m×m  orthogonal — left singular vectors  (eigenvectors of A Aᵀ)
#   Σ  : m×n  diagonal   — singular values        (sqrt of eigenvalues of AᵀA)
#   Vᵀ : n×n  orthogonal — right singular vectors (eigenvectors of AᵀA)
#
# Manual derivation sketch (educational):
#   1. Form the n×n symmetric PSD matrix M = AᵀA
#   2. Eigen-decompose M = V Λ Vᵀ   (eigenvalues λᵢ ≥ 0)
#   3. Singular values:  σᵢ = √λᵢ
#   4. Right singular vectors: columns of V (from step 2)
#   5. Left singular vectors:  uᵢ = A vᵢ / σᵢ  for σᵢ > 0

def svd_manual(A):
    """
    Compute the full SVD of A via eigen-decomposition of AᵀA.
    Returns U (m×m), S (k,), Vt (n×n)  — same convention as np.linalg.svd.

    Note: np.linalg.svd is more numerically stable; this is for pedagogy.
    """
    m, n = A.shape
    k = min(m, n)

    # Step 1-2: eigen-decompose AᵀA  (symmetric → real eigenvalues)
    M = A.T @ A                                     # (n×n)
    eigenvalues, V = np.linalg.eigh(M)              # eigh for symmetric matrix

    # Step 3: sort by descending eigenvalue
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx]
    V = V[:, idx]                                   # columns are right sing. vecs

    # Step 4: singular values (clip tiny negatives caused by floating point)
    S = np.sqrt(np.maximum(eigenvalues[:k], 0.0))

    # Step 5: left singular vectors  uᵢ = A vᵢ / σᵢ
    U = np.zeros((m, m))
    for i in range(k):
        if S[i] > 1e-12:
            U[:, i] = A @ V[:, i] / S[i]
        # else: σᵢ ≈ 0 → uᵢ is in null-space of A (fill in below)

    # Extend U to a full orthonormal basis for ℝᵐ via Gram–Schmidt on the null-space
    rank = int(np.sum(S > 1e-12))
    if rank < m:
        # Complete U with vectors orthogonal to the existing columns
        null_basis = _null_space_completion(U[:, :rank], m)
        U[:, rank:] = null_basis

    Vt = V.T                                        # (n×n)
    return U, S, Vt


def _null_space_completion(Q, target_dim):
    """Return (target_dim - Q.shape[1]) orthonormal vectors orthogonal to Q."""
    existing = Q.shape[1]
    extra = target_dim - existing
    if extra <= 0:
        return np.empty((target_dim, 0))
    # Random vectors → QR to complete the basis
    rng = np.random.default_rng(seed=42)
    candidates = np.hstack([Q, rng.standard_normal((target_dim, extra + 5))])
    full_Q, _ = np.linalg.qr(candidates, mode="complete")
    return full_Q[:, existing : existing + extra]


# ── Validation suite ───────────────────────────────────────────────────────────

def validate_svd(A, label="", use_manual=False):
    """Run all SVD correctness checks on matrix A."""
    print(f"\n{'─'*60}")
    print(f"  Matrix: {label}  shape={A.shape}  dtype={A.dtype}")
    print(f"{'─'*60}")

    if use_manual:
        U, S, Vt = svd_manual(A)
        print("  (using manual SVD via AᵀA eigen-decomposition)")
    else:
        U, S, Vt = np.linalg.svd(A, full_matrices=True)
        print("  (using np.linalg.svd reference)")

    m, n = A.shape
    k = min(m, n)
    Sigma = np.zeros((m, n))
    Sigma[:k, :k] = np.diag(S)

    # ── Check 1: Reconstruction ────────────────────────────────────────────────
    A_reconstructed = U @ Sigma @ Vt
    allclose(A, A_reconstructed,  label="Reconstruction:  A ≈ U Σ Vᵀ")

    # ── Check 2: U orthogonality ───────────────────────────────────────────────
    allclose(U.T @ U, np.eye(m),  label="U orthogonality: UᵀU ≈ I")

    # ── Check 3: V orthogonality ───────────────────────────────────────────────
    V = Vt.T
    allclose(V.T @ V, np.eye(n),  label="V orthogonality: VᵀV ≈ I")

    # ── Check 4: singular values non-negative & sorted descending ──────────────
    non_neg = bool(np.all(S >= -1e-12))
    sorted_desc = bool(np.all(np.diff(S) <= 1e-12))
    print(f"  [{'PASS' if non_neg else 'FAIL'}] Singular values >= 0")
    print(f"  [{'PASS' if sorted_desc else 'FAIL'}] Singular values sorted descending")
    print(f"  S = {np.round(S, 4)}")

    return U, S, Vt


# ── Low-rank approximation ─────────────────────────────────────────────────────

def low_rank_approx(A, rank):
    """Return the best rank-r approximation of A (Eckart-Young theorem)."""
    U, S, Vt = np.linalg.svd(A, full_matrices=False)   # economy SVD
    # Keep only the top-r components
    U_r  = U[:,  :rank]                                 # (m, r)
    S_r  = S[    :rank]                                 # (r,)
    Vt_r = Vt[  :rank, :]                               # (r, n)
    A_r  = U_r @ np.diag(S_r) @ Vt_r
    return A_r


def demo_low_rank():
    print(f"\n{'='*60}")
    print("  Low-rank approximation demo  (Eckart-Young theorem)")
    print(f"{'='*60}")

    rng = np.random.default_rng(seed=0)
    # Build a rank-3 matrix + small noise  ->  good low-rank structure
    m, n, true_rank = 20, 15, 3
    L = rng.standard_normal((m, true_rank))
    R = rng.standard_normal((true_rank, n))
    A = L @ R + 0.1 * rng.standard_normal((m, n))

    frob_A = np.linalg.norm(A, "fro")
    print(f"\n  Original matrix  shape={A.shape}  ||A||_F={frob_A:.4f}")
    print(f"  True rank used to generate A: {true_rank}\n")

    for r in [1, 2, 3, 5, min(m, n)]:
        A_r = low_rank_approx(A, r)
        err = np.linalg.norm(A - A_r, "fro")
        rel = err / frob_A
        print(f"  rank-{r:2d} approx:  ||A - A_r||_F = {err:.4f}  "
              f"(relative {rel:.1%})")

    # Verify optimal error equals tail singular values (Eckart-Young)
    print("\n  Eckart-Young verification:")
    _, S, _ = np.linalg.svd(A, full_matrices=False)
    for r in [1, 2, 3]:
        A_r = low_rank_approx(A, r)
        actual_err   = np.linalg.norm(A - A_r, "fro")
        optimal_err  = np.sqrt(np.sum(S[r:] ** 2))     # sigma_{r+1}^2 + ... + sigma_k^2
        match = "OK" if abs(actual_err - optimal_err) < 1e-9 else "FAIL"
        print(f"  rank-{r}  actual_err={actual_err:.6f}  "
              f"sqrt(sum(sigma_i^2 for i>{r}))={optimal_err:.6f}  [{match}]")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    rng = np.random.default_rng(seed=7)

    test_cases = [
        ("square  4x4",  rng.standard_normal((4, 4))),
        ("tall    6x3",  rng.standard_normal((6, 3))),
        ("wide    3x6",  rng.standard_normal((3, 6))),
        ("square  5x5 (manual)", rng.standard_normal((5, 5))),
        ("tall    8x3 (manual)", rng.standard_normal((8, 3))),
    ]

    for label, A in test_cases:
        use_manual = "manual" in label
        validate_svd(A, label=label, use_manual=use_manual)

    demo_low_rank()


if __name__ == "__main__":
    main()
