# Exp 02 public export sanitization

The privately collected raw file contained a machine-local model path. Before
creating the public-safe export, the private raw artifact was fingerprinted in
local-only provenance storage.

The deterministic export replaces only that known path with the checkpoint
identifier `Qwen3-Coder-30B-A3B-Instruct-MLX-4bit`. Numerical measurements,
run identifiers, timestamps, prompt hashes, and all other experimental metadata
remain unchanged. The sanitizer fails rather than removing any unrecognized
machine-local path.
