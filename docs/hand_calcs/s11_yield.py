"""Hand calculations for model card §11 (statistical budget and yield). Standard library only."""

from math import erfc, sqrt

m_mean = (0.0 - (1.5 + 0.0004 + 1.0 + 0.0004 + 1.5) + 6.0) - 1.5
sigma_total = sqrt(3 * 0.2**2)
z = m_mean / sigma_total
phi = 0.5 * erfc(-z / sqrt(2))
print(f"M_mean {m_mean:.4f} dB, sigma_total {sigma_total:.5f} dB, z {z:.5f}, yield {phi:.5f}")
print(f"margin at 3 sigma {m_mean - 3 * sigma_total:.5f} dB")
print(f"Monte Carlo standard error at 1e6 samples {sqrt(phi * (1 - phi) / 1e6):.6f}")
