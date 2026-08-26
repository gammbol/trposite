# Apply final stabilization patch

Apply from the repository root after the test-cluster patch:

```bash
tar -xf trposite_final_stabilization_patch.tar
```

Then run:

```bash
cd backend
python -m pip install -r requirements-test.txt
cd ..
./scripts/run_test_cluster.sh
```

This patch intentionally modifies only the verification/consensus/LLM reliability
code and adds regression documentation/tests.
