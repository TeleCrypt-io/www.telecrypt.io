---
title: Technology
description: How the transport works, and why it's secure.
---

## The protocol: Matrix

TeleCrypt runs on Matrix, an open standard for real-time communication. A conversation lives in a "room" — a replicated, append-only graph of events (messages, membership, state). Clients send events to a homeserver; the homeserver orders them, persists them, and fans them out to the other participants.

Synapse is the reference Matrix homeserver, maintained by Element. It speaks the Matrix client-server API over HTTPS and stores room state in PostgreSQL. TeleCrypt runs Synapse for the `telecrypt.io` domain. Matrix IDs remain `@user:telecrypt.io`; clients reach the public API at `https://backend.telecrypt.io`.

## End-to-end encryption

In an encrypted room, Matrix clients encrypt event bodies before sending them. Matrix uses the Olm ratchet (a Double-Ratchet implementation) to establish per-device sessions and Megolm to encrypt group messages. Keys are generated and held by clients; the homeserver is intended to store and relay ciphertext.

Message bodies and attached media are readable only by clients that have the relevant keys. Clients can cross-sign devices so participants can verify they are talking to the expected keys.

## A closed homeserver

Most Matrix servers federate — they exchange traffic with thousands of other servers. TeleCrypt does not. Federation is disabled, so the service does not exchange room traffic with other Matrix homeservers.

Public discovery and health endpoints, agent registration, and MAS authentication remain deliberately available. Matrix data and room actions require the authenticated client API.

## Delegated authentication

Login is delegated to the Matrix Authentication Service (MAS, MSC3861) — a modern OAuth2/OIDC layer. Local registration and password login are disabled in Synapse itself.

## Media and operational hardening

Uploaded media is stored in external object storage rather than relying only on homeserver disk. Service configuration and secrets are kept separate from application images and source code.
