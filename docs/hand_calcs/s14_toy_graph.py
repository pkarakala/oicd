"""Hand calculations for the model card §14.1 toy graph (the inference-engine test case).
Standard library only."""

power_w, rate_tbps = 30.0, 6.4
for factor in (1, 2):
    print(
        f"direction factor {factor}: energy = 30 W / {rate_tbps * factor} Tbps =",
        power_w / (rate_tbps * factor),
        "pJ/bit",
    )
e1, e2 = power_w / rate_tbps, power_w / (2 * rate_tbps)
print("interval over the factor range [1, 2]: lo", min(e1, e2), "hi", max(e1, e2))
print("gap to the 5 pJ/bit claim at factor 1:", abs(e1 - 5) / 5, "(tolerance 0.10)")
print("gap to the 3.0 pJ/bit copy at factor 1:", abs(e1 - 3) / 3, "(tolerance 0.25)")
print("gap to the 5 pJ/bit claim at factor 2:", abs(e2 - 5) / 5)
print("gap to the 3.0 pJ/bit copy at factor 2:", abs(e2 - 3) / 3)
print("widths 26.4 vs 27.6 mm: gap", abs(26.4 - 27.6) / 27.6, "(tolerance 0.01)")
print("tornado swing of the factor:", abs(e2 - e1))
print("8 x 13 mW =", 8 * 13, "mW against the 100 mW minimum")
