import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statsmodels.stats.contingency_tables import mcnemar
from statsmodels.stats.proportion import proportion_confint

# Results from your evaluations
llm_correct = [1,1,1,0,0,0,1,0,1,0,1,1,1,1,1,1,1,1,0,1,0,1,1,0,1,0,1,1,1,1]
xgb_correct = [1,1,0,1,1,1,1,1,0,1,0,1,1,1,0,0,1,1,1,1,1,1,0,1,1,1,0,1,1,1]

n = 30

# McNemar's test
both =     sum(1 for l,x in zip(llm_correct,xgb_correct) if l==1 and x==1)
llm_only = sum(1 for l,x in zip(llm_correct,xgb_correct) if l==1 and x==0)
xgb_only = sum(1 for l,x in zip(llm_correct,xgb_correct) if l==0 and x==1)
neither =  sum(1 for l,x in zip(llm_correct,xgb_correct) if l==0 and x==0)

table = [[both, llm_only], [xgb_only, neither]]
result = mcnemar(table, exact=True)

print(f"McNemar's test p-value: {result.pvalue:.4f}")
print("Statistically significant!" if result.pvalue < 0.05
      else "Not statistically significant (p=0.80, n=30 too small)")

# Confidence intervals
print("\n95% Confidence Intervals:")
for name, k in [("Pure LLM", 21), ("XGBoost", 23), ("Hybrid", 23)]:
    lo, hi = proportion_confint(k, n, method='wilson')
    print(f"  {name}: {k/n:.1%} (95% CI: {lo:.1%}–{hi:.1%})")