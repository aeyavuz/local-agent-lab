# Broken Calculator Seed

This immutable fixture supports Local Agent Lab experiments 03 and 04. Its
canonical validation command is `make gates`.

It intentionally contains one deterministic defect: the median of an
even-length sequence returns the upper middle value rather than the average of
the two middle values. Do not modify this seed; benchmark runs use disposable
copies.
