# SYNTHETIC — NOT QUALIFICATION EVIDENCE

All cases, issuers, offerings and publisher records here are invented test data.
They NEVER qualify any publisher, satisfy R7/R8, or enable production admission.
The three cases cover two issuers and two offerings for the same issuer. They
are NOT genuine source-backed positive baselines or canonical production inputs.

`tests/gmp_mechanics_harness.py` materializes their explicitly labelled files and
A28.1 format-only envelopes into pytest temporary directories. No fake authority
record is added to handoff/decisions or a real source package. The harness is
TEST ONLY, never imported by engine code, and reports `production_admission=False`
for every mechanics-positive. Its scenario declarations are not new closed-schema
fields or a production conflict/withdrawal verifier.

The engine helper under test validates declared file-byte pins ONLY. Passing its
checks for a fake labelled qualification document demonstrates precisely why
integrity must remain distinct from authority, source facts and Final eligibility.
Replay tests re-read saved bytes/declarations without querying live publishers;
production evaluation replay and its fail-closed boundary remain separately tested.
