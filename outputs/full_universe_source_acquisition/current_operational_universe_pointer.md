# Current Operational Universe Pointer

Pointer created by: `v2.22B`  
Pointer type: `single_live_operational_universe_reference`

## Current dataset

`outputs\full_universe_source_acquisition\expanded_universe_v2_21h_activated_operational_reference.csv`

Rows: `43089`  
SHA256: `9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707`

## Previous operational base

`outputs\full_universe_source_acquisition\expanded_universe_v2_20m_asx_promoted.csv`

Rows: `42708`  
SHA256: `892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127`

## Rollback dataset

`outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv`

Rows: `38287`  
SHA256: `cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f`

## Policy

- This file defines the single current operational universe pointer.
- Consumers should read the pointer JSON before audit or scoring.
- Pointer updates require an explicit gate.
- Dataset overwrites are not allowed.
- Scoring, OpenAI, broker calls, and full59k remain unauthorized unless separately approved.
