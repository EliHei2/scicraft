# tabmodel

A pretrained model for classification on tables.

## Install

```bash
pip install tabmodel
```

## Quickstart

```python
from tabmodel import TabClassifier
clf = TabClassifier()
clf.fit(X_train, y_train)
pred = clf.predict(X_test)
```

## License

MIT
