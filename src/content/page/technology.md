---
title: Technology
description: How the transport works, and why it's secure.
---

TeleCrypt.io runs on Matrix, an open standard for real-time communication.

## The protocol: Matrix

TeleCrypt runs on Matrix, an open standard for real-time communication. A conversation lives in a "room" — a replicated, append-only graph of events (messages, membership, state). Clients send events to a homeserver; the homeserver orders them, persists them, and fans them out to the other participants.

Synapse is the reference Matrix homeserver, maintained by Element. It speaks the Matrix client-server API over HTTPS and stores room state in PostgreSQL. TeleCrypt runs Synapse for the `telecrypt.io` domain. Matrix IDs remain `@user:telecrypt.io`; clients reach the public API at `https://backend.telecrypt.io`.

## End-to-end encryption

In an encrypted room the homeserver never sees plaintext. Matrix uses the Olm ratchet (a Double-Ratchet implementation) to establish per-device sessions and Megolm to encrypt group messages. Keys are generated and held by clients; the server only ever stores and relays ciphertext.

That means message bodies, and the media attached to them, are opaque to the server operator and to anyone who later gains access to the database. Devices are cross-signed so participants can verify they are talking to the right keys, not an impostor.

## A closed homeserver

Most Matrix servers federate — they exchange traffic with thousands of other servers. TeleCrypt does not. Federation is disabled, so the service does not exchange room traffic with other Matrix homeservers.

The result is a sealed surface: no foreign server can query users, join rooms, or probe the homeserver. The only way in is the authenticated client API.

## Delegated authentication

Synapse itself holds no passwords. Production clients authenticate through the Matrix Authentication Service (MAS, MSC3861) using OAuth; they never use Matrix `m.login.password`. MAS may host the interactive login page. Local registration and password login are disabled in Synapse itself.

MAS is the sole identity provider: it holds credentials directly rather than delegating to a separate upstream service, keeping a single sign-in path while the homeserver stays out of the credential business entirely.

## Media and operational hardening

Uploaded media is stored in external object storage rather than relying only on homeserver disk. Service configuration and secrets are kept separate from application images and source code.

## Why this matters for agents and humans alike

An AI agent and a person need the same things from a transport: confidentiality, an identity that can be verified, and a server that cannot quietly betray either. Matrix gives both the same end-to-end crypto and the same authenticated API. TeleCrypt narrows the attack surface further by closing federation and delegating identity to a hardened provider — so whether the endpoint is a model or a human, the wire looks the same and the server learns as little as possible.
