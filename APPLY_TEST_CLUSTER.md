# Apply test cluster patch

Extract this archive from the root of `trposite` after the verification and
consensus-engine patches have been applied.

```bash
tar -xf trposite_test_cluster_patch.tar
```

Install test dependencies:

```bash
cd backend
python -m pip install -r requirements-test.txt
cd ..
```

Run the complete cluster:

```bash
./scripts/run_test_cluster.sh
```

The cluster does not require OpenAI, DeepSeek or Ollama to be available for its
automated integration/resilience tests. External providers are replaced with
controlled fakes where appropriate.
