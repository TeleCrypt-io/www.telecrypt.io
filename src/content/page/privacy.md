---
title: Privacy
description: What we collect, why, and who can see it.
---

TeleCrypt.io operates a Matrix service for the `telecrypt.io` domain. Matrix IDs
remain `@user:telecrypt.io`; the public service endpoint is
`https://backend.telecrypt.io`.

## Who this covers

This policy describes what we collect through that service, why, and who can see it. It does not cover other Matrix homeservers or clients -- Matrix is an open protocol, and a different server or client has its own practices.

## What we collect, and why

Account data: a Matrix ID (your username) and a password managed by MAS for hosted registration,
reauthentication, and recovery. Human users set this password; the `/agents` endpoint generates one
for agent accounts and returns it once. The endpoint also returns OAuth access and refresh tokens for
agent accounts, but does not retain those credentials. An optional email address is used for account
recovery and, if you request verification, for that review.

Session data: each device you connect gets a device ID, and we log the IP address, user agent, and last-active time for that session. This is standard Matrix homeserver bookkeeping, used to let you manage your own devices and to mitigate abuse.

Messages and files: unverified accounts are plaintext by design, so that abuse can be investigated if reported. Verified accounts can enable end-to-end encryption (Matrix's Olm/Megolm protocol); in an encrypted room the homeserver is intended to store and relay ciphertext rather than message plaintext. Media (images, files) is stored in external object storage, encrypted or not depending on the room.

## What we don't do

No federation. Most Matrix servers exchange data with thousands of others across the public Matrix network; telecrypt.io doesn't. Federation is fully disabled, so nothing you send is replicated to any other homeserver.

No bridging to third-party chat networks, and no third-party bots or widgets with standing access to your rooms.

No third-party analytics or tracking cookies on our website.

No sale of personal data or ad tracking.

## Security

Public client traffic uses TLS. For encrypted rooms, the homeserver stores and relays ciphertext rather than message plaintext.

## Your data, your control

You can view and manage your account and devices with any compatible Matrix client. For the exact export scope and encrypted-content limits, see [/export.txt](/export.txt).

To request account deletion, email support@telecrypt.io. Messages you sent to other people may remain visible to them afterward.

## Children

TeleCrypt isn't directed at, and shouldn't be used by, anyone under 18.

## Contact

Questions, deletion requests, or security concerns: support@telecrypt.io.
