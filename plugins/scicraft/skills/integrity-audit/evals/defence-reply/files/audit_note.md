# Questions on the leakage score (internal review)

1. Is the leakage score computed with the same threshold for every model, or was it tuned after seeing our results?
2. The score clips negative values to zero. Does the clip change which model ranks first?
3. Does the score favor our model? Show me a case where it does not.
