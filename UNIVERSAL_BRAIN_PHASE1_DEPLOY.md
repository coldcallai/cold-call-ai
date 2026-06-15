UniversalBrain Phase 1 — VPS Deploy Instructions
================================================

This bundle is ADDITIVE and NON-BREAKING:
  - Adds new directories: universal/, playbooks/, tests/universal/, tests/playbooks/
  - Does NOT touch server.py, .env, or any production code path
  - Feature flag UNIVERSAL_BRAIN_ENABLED defaults to false
  - You DO NOT need to restart pm2 after deploy
  - Production inbound call flow is unaffected


STEP 1 — Save the base64 bundle to your VPS
--------------------------------------------
On your VPS, paste the entire contents of `universal_brain_phase1.b64`
into a single file:

    nano /tmp/ubp1.b64
    # paste, save (Ctrl+O, Enter, Ctrl+X)

The file is 30 KB. Any modern terminal handles a single-line paste of
that size. (If your terminal mangles long lines, use the file-transfer
method below instead.)


STEP 2 — Decode, extract, and run all 4 health tests (one-liner)
----------------------------------------------------------------
    cd /var/www/dialgenix/backend && base64 -d /tmp/ubp1.b64 | tar -xzvf - && PYTHONPATH=$PWD python3 tests/universal/test_schema_lock.py && PYTHONPATH=$PWD python3 tests/universal/test_deletion_independence.py && PYTHONPATH=$PWD python3 tests/universal/test_no_industry_logic.py && PYTHONPATH=$PWD python3 tests/playbooks/test_merchant_brain.py


EXPECTED OUTPUT (all 4 suites must report PASS):
    PASS: all schemas locked
    PASS: test_universal_imports_without_any_playbook
    PASS: test_orchestrator_runs_with_noop_playbook
    PASS: test_no_industry_in_conditionals
    PASS: test_decision_maker_count_v1
    PASS: test_funding_question_count_v1
    PASS: test_gatekeeper_shipped
    PASS: test_jargon_map_present
    PASS: test_no_jargon_in_caller_facing_phrasings
    PASS: test_qualification_question_count_v1
    PASS: test_transfer_bands_contiguous
    PASS: test_transfer_signal_phrases_non_empty
    PASS: test_workflow_question_count_v1


STEP 3 — Verify (optional smoke test)
-------------------------------------
    cd /var/www/dialgenix/backend && PYTHONPATH=$PWD python3 -c "
    from playbooks.merchant_brain import MerchantBrain, GATEKEEPER_STATUS
    from universal.contracts.playbook import LIB_WORKFLOW, LIB_FUNDING, LIB_QUALIFICATION
    mb = MerchantBrain()
    print(f'  decision_maker triggers : {len(mb.get_triggers())}')
    print(f'  workflow questions     : {len(mb.get_questions(LIB_WORKFLOW))}')
    print(f'  funding questions      : {len(mb.get_questions(LIB_FUNDING))}')
    print(f'  qualification questions: {len(mb.get_questions(LIB_QUALIFICATION))}')
    print(f'  transfer decisions     : {len(mb.get_transfer_decisions())}')
    print(f'  transfer signals       : {len(mb.get_transfer_signals())}')
    print(f'  jargon entries         : {len(mb.get_jargon_map())}')
    print(f'  GATEKEEPER_STATUS      : {GATEKEEPER_STATUS}')
    "


WHAT IS NOW LIVE-DEPLOYABLE
---------------------------
1. /var/www/dialgenix/backend/universal/                  — 10 engines + contracts
2. /var/www/dialgenix/backend/playbooks/merchant_brain/   — V1 content
       Decision Maker V1  : 8 triggers     [SHIPPED]
       Gatekeeper V1      : 15 triggers    [SHIPPED]
       Workflow V1        : 10 questions   [SHIPPED]
       Funding V1         : 10 questions   [SHIPPED]
       Qualification V1   : 8 questions    [SHIPPED]
       Transfer V1        : 3 bands + 13 signals [SHIPPED]
       Jargon Map         : 25 entries     [SHIPPED]
3. /var/www/dialgenix/backend/tests/                      — 4 test suites


WHAT IS NOT YET LIVE
--------------------
- The Orchestrator does NOT replace the existing inline brain in server.py.
- It is feature-flagged with UNIVERSAL_BRAIN_ENABLED=false by default.
- Wiring server.py to call Orchestrator.handle_turn() is a separate Phase 2
  task (after Gatekeeper V1 content arrives + first live-call validation).


ROLLBACK (if anything looks wrong)
----------------------------------
    rm -rf /var/www/dialgenix/backend/universal
    rm -rf /var/www/dialgenix/backend/playbooks/merchant_brain
    rm -rf /var/www/dialgenix/backend/tests/universal
    rm -rf /var/www/dialgenix/backend/tests/playbooks

Nothing else needs reverting — server.py is untouched.
